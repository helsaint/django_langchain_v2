from django.shortcuts import render
from django.http import JsonResponse
from .utils.nl_sql import sql_chain
from .utils.vector import vector_chain
from django.views.decorators.csrf import csrf_exempt  

@csrf_exempt
def nl_sql_executor(request):
    if request.method == "POST":
        nl = request.POST.get("nl", "")
        nl = nl.lower()
        #result = sql_chain.invoke({"question": nl})
        result = vector_chain.invoke({"question": nl})
        print(result)
        return JsonResponse({"message": [result['answer']]})
    return render(request, "nl_executor.html")
# Create your views here.