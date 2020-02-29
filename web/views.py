from django.shortcuts import render
from django.http import HttpRequest
from celery.decorators import task
import dataclasses

from tlsprofiler import TLSProfiler, TLSProfilerResult

# Create your views here.

_PROFILES = ["modern", "intermediate", "old"]


@task(name="run_tls_profiler")
def run_scan(domain: str, profile: str) -> TLSProfilerResult:
    profiler = TLSProfiler(domain, profile)
    result = profiler.run()
    result = dataclasses.asdict(result)
    return result


def index(request: HttpRequest):
    if "domain" in request.GET and "profile" in request.GET:
        domain = request.GET["domain"]
        profile = request.GET["profile"]
        if domain and profile in _PROFILES:
            print(domain)
            print(profile)
            task_result = run_scan.delay(domain, profile)
            result = task_result.get()
            return render(request, "index.html", {"result": result})

    return render(request, "index.html")
