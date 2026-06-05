from django.contrib import admin
from .models import Customer, Product, Order, QueryLog


@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    list_display = ["short_question", "was_blocked", "row_count", "created_at"]
    list_filter = ["was_blocked"]
    readonly_fields = ["question", "generated_sql", "safe_sql",
                       "was_blocked", "block_reason", "row_count", "created_at"]

    def short_question(self, obj):
        return obj.question[:80]
    short_question.short_description = "Question"


admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Order)