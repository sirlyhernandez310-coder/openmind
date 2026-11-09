from django.contrib import admin

from .models import Answer, Evaluation, Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("order", "text", "dimension", "is_critical", "is_active")
    list_editable = ("is_active",)
    list_filter = ("dimension", "is_active")


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question", "value")
    can_delete = False


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "percentage", "level", "needs_support")
    list_filter = ("level", "needs_support")
    search_fields = ("user__email",)
    readonly_fields = [f.name for f in Evaluation._meta.fields]
    inlines = (AnswerInline,)
