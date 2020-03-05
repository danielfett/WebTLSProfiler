from django.shortcuts import render
from django.http import HttpRequest
from celery.decorators import task
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


def index(request: HttpRequest):
    domain = ""
    profile = ""
    result = None

    if "domain" in request.GET:
        domain = request.GET["domain"]

    if "profile" in request.GET:
        profile = request.GET["profile"]

    if validators.domain(domain) and profile in _PROFILES:
        print(f"Scan domain {domain} with the profile {profile}")
        task_result = run_scan.delay(domain, profile)
        result = task_result.get()

    return render(
        request,
        "index.html",
        {"result": result, "domain_name": domain, "profile_name": profile},
    )
