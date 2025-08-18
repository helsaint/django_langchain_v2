from django.shortcuts import render
from django.http import JsonResponse
from .utils.nl_sql import sql_chain

def nl_sql_executor(request):

    if request.method == "POST":
        nl = request.POST.get("nl", "")
        nl = nl.lower()
        result = sql_chain.invoke({"question": nl})
        return JsonResponse({"message": [result['answer'],]})
    return render(request, "nl_executor.html")
# Create your views here.
