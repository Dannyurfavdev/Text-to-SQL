import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import QueryLog
from .services.generator import generate_sql
from .services.guardrails import apply_guardrails, check_question_intent, GuardrailError
from .services.executor import execute_query

from django.shortcuts import render
from django.conf import settings


@method_decorator(csrf_exempt, name="dispatch")
class QueryView(View):

    def post(self, request):
        body = json.loads(request.body)
        question = body.get("question", "").strip()

        if not question:
            return JsonResponse({"error": "question is required"}, status=400)

        # Check intent BEFORE calling the LLM
        try:
            check_question_intent(question)
        except GuardrailError as e:
            QueryLog.objects.create(
                question=question,
                generated_sql="",
                was_blocked=True,
                block_reason=str(e),
            )
            return JsonResponse({
                "blocked": True,
                "reason": str(e),
                "generated_sql": None,
            }, status=400)

        # Now safe to call the LLM

        # Step 1: Generate SQL from the question
        raw_sql = generate_sql(question)

        # Step 2: Run guardrails
        try:
            safe_sql = apply_guardrails(raw_sql)
        except GuardrailError as e:
            QueryLog.objects.create(
                question=question,
                generated_sql=raw_sql,
                was_blocked=True,
                block_reason=str(e),
            )
            return JsonResponse({
                "blocked": True,
                "reason": str(e),
                "generated_sql": raw_sql,
            }, status=400)

        # Step 3: Execute safely
        results = execute_query(safe_sql)

        QueryLog.objects.create(
            question=question,
            generated_sql=raw_sql,
            safe_sql=safe_sql,
            was_blocked=False,
            row_count=results["row_count"],
        )

        return JsonResponse({
            "blocked": False,
            "question": question,
            "sql": safe_sql,
            "columns": results["columns"],
            "rows": results["rows"],
            "row_count": results["row_count"],
        })


class FrontendView(View):
    def get(self, request):
        return render(request, "sql_app/frontend.html")


class SchemaInfoView(View):
    def get(self, request):
        from .services.schema import get_schema_description
        table_count = len(settings.ALLOWED_TABLES)
        return JsonResponse({
            "table_count": table_count,
            "tables": settings.ALLOWED_TABLES,
        })