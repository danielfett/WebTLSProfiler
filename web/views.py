from typing import Tuple

from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from celery.decorators import task
from celery.result import AsyncResult
import dataclasses
import validators

from tlsprofiler import TLSProfiler, TLSProfilerResult


_PROFILES = ["modern", "intermediate", "old"]


@task(name="run_tls_profiler")
def run_scan(domain: str, profile: str) -> TLSProfilerResult:
    profiler = TLSProfiler(domain, profile)
    result = profiler.run()
    result = dataclasses.asdict(result)
    return result


def process_request_data(request: HttpRequest) -> Tuple[str, str, str, str]:
    domain = ""
    sess_domain = ""
    profile = ""
    sess_profile = ""

    if "domain" in request.GET:
        domain = request.GET["domain"]

    if "domain" in request.session:
        sess_domain = request.session["domain"]

    if "profile" in request.GET:
        profile = request.GET["profile"]

    if "profile" in request.session:
        sess_profile = request.session["profile"]

    return domain, sess_domain, profile, sess_profile


def index(request: HttpRequest):
    result = None

    domain, sess_domain, profile, sess_profile = process_request_data(request)

    if "task_id" in request.session:
        task_id = request.session["task_id"]
        async_result = AsyncResult(task_id)
        result = async_result.result

    return render(
        request,
        "index.html",
        {"result": result, "domain_name": sess_domain, "profile_name": sess_profile},
    )


def start_task(request: HttpRequest):
    domain, sess_domain, profile, sess_profile = process_request_data(request)

    if (
        validators.domain(domain)
        and profile in _PROFILES
        and (domain != sess_domain or profile != sess_profile)
    ):
        # terminate an already running task
        if "task_id" in request.session:
            task_id = request.session["task_id"]
            async_result = AsyncResult(task_id)
            if not async_result.ready():
                async_result.revoke(terminate=True)

        print(f"Scan domain {domain} with the profile {profile}")
        task_result = run_scan.delay(domain, profile)

        request.session["task_id"] = task_result.id
        request.session["domain"] = domain
        request.session["profile"] = profile

        return HttpResponse("1")

    return HttpResponse("0")


def task_ready(request: HttpRequest):
    if "task_id" in request.session:
        task_id = request.session["task_id"]
        async_result = AsyncResult(task_id)
        if async_result.ready():
            return HttpResponse("1")

    return HttpResponse("0")
