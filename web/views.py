from typing import Tuple

from django.shortcuts import render, get_object_or_404
from django.http import HttpRequest, HttpResponse, JsonResponse
from celery.decorators import task
from celery.result import AsyncResult
import dataclasses
import validators
from datetime import datetime, timedelta
from django.utils import timezone

from tlsprofiler import TLSProfiler, TLSProfilerResult

# class TLSProfilerResult:
#    ...

from .models import Scan


_PROFILES = ["modern", "intermediate", "old"]

EXPIRE_SCANS_AFTER = timedelta(minutes=15)
MAX_WAITING_SCANS = 10
NUM_RECENT_SCANS = 10


@task(name="run_tls_profiler")
def run_scan(domain: str, profile: str) -> TLSProfilerResult:
    result = None
    try:
        profiler = TLSProfiler(domain, profile)
        result = profiler.run()
    except Exception as e:
        return {"error": e}

    if result is None:
        return {"error": profiler.server_error}

    return dataclasses.asdict(result)


def process_request_data(request: HttpRequest) -> Tuple[str, str, str, str, bool]:
    domain = ""
    sess_domain = ""
    profile = ""
    sess_profile = ""
    is_public = False

    if "domain" in request.GET:
        domain = request.GET["domain"]

    if "domain" in request.session:
        sess_domain = request.session["domain"]

    if "profile" in request.GET:
        profile = request.GET["profile"]

    if "profile" in request.session:
        sess_profile = request.session["profile"]

    if "is_public" in request.GET:
        is_public = request.GET["is_public"] == "true"

    return domain, sess_domain, profile, sess_profile, is_public


def waiting_scans():
    return Scan.objects.filter(end_datetime=None,).count()


def index(request: HttpRequest):
    expire_old_scans()

    result = None

    domain, sess_domain, profile, sess_profile, is_public = process_request_data(
        request
    )

    if "task_id" in request.session:
        task_id = request.session["task_id"]
        async_result = AsyncResult(task_id)
        result = async_result.result
        async_result.forget()
        del request.session["task_id"]

    recent_scans = (
        Scan.objects.filter(end_datetime__isnull=False, is_public=True,)
        .order_by("-start_datetime")[:NUM_RECENT_SCANS]
        .values_list("domain", flat=True)
    )

    return render(
        request,
        "index.html",
        {
            "result": result,
            "domain_name": sess_domain,
            "profile_name": sess_profile,
            "is_public": is_public,
            "waiting_scans": waiting_scans(),
            "max_waiting_scans": MAX_WAITING_SCANS,
            "recent_scans": recent_scans,
        },
    )


def start_task(request: HttpRequest):
    domain, sess_domain, profile, sess_profile, is_public = process_request_data(
        request
    )

    if waiting_scans() > MAX_WAITING_SCANS:
        return JsonResponse(
            {"error": "Too many scans in queue, please try again later."}
        )

    if validators.domain(domain) and profile in _PROFILES:
        # terminate an already running task
        if "task_id" in request.session:
            task_id = request.session["task_id"]
            async_result = AsyncResult(task_id)
            if not async_result.ready():
                async_result.revoke(terminate=True)
                try:
                    db_scan = Scan.objects.get(task_id=task_id)
                except Scan.DoesNotExist:
                    pass
                else:
                    db_scan.delete()

        print(f"Scan domain {domain} with the profile {profile}")
        task_result = run_scan.delay(domain, profile)

        scan = Scan(
            domain=domain, profile=profile, is_public=is_public, task_id=task_result.id,
        )
        scan.save()

        request.session["task_id"] = task_result.id
        request.session["domain"] = domain
        request.session["profile"] = profile

        return JsonResponse({"error": ""})

    return JsonResponse({"error": "Please enter a valid domain and select a profile"})


def expire_old_scans():
    Scan.objects.filter(
        end_datetime=None, start_datetime__lt=timezone.now() - EXPIRE_SCANS_AFTER,
    ).delete()


def task_ready(request: HttpRequest):
    expire_old_scans()
    if "task_id" in request.session:
        task_id = request.session["task_id"]
        async_result = AsyncResult(task_id)
        try:
            scan = Scan.objects.get(task_id=task_id)
        except Scan.DoesNotExist:
            return JsonResponse({"finished": True, "status": "Task not found"})

        if async_result.ready():
            scan.end_datetime = timezone.now()
            scan.save()
            return JsonResponse({"finished": True})
        else:
            before = (
                Scan.objects.exclude(task_id=scan.task_id,)
                .filter(start_datetime__lt=scan.start_datetime, end_datetime=None,)
                .count()
            )
            if before > 9:
                return JsonResponse(
                    {
                        "finished": False,
                        "status": f"Waiting in queue ({before} scan(s) before yours)",
                    }
                )
            else:
                return JsonResponse({"finished": False, "status": f"Scanning..."})

    return JsonResponse(
        {"finished": True}
    )  # will reload page if not task is in session
