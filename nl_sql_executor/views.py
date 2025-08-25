from django.shortcuts import render
from django.http import JsonResponse
from .utils.nl_sql import sql_chain
from .utils.vector import vector_chain
from .utils.query_routing import router
from django.views.decorators.csrf import csrf_exempt  


@csrf_exempt
def nl_sql_executor(request):
    
    if request.method == "POST":
        nl = request.POST.get("nl", "")
        nl = nl.lower()
        route = router.invoke({"question": nl})
        result = {}
        if route['datasource'] == "POSTGRESQL":
            result = sql_chain.invoke({"question": nl})
        #result = sql_chain.invoke({"question": nl})
        elif route['datasource'] == "FAISS":
            result = vector_chain.invoke({"question": nl})
        else:
            result = {"answer": "Unable to determine the appropriate data source."}
        #print(result)
        return JsonResponse({"message": [result['answer'],route['datasource'],]})
    return render(request, "nl_executor.html")
# Create your views here.