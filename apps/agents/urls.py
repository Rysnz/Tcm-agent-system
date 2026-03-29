from django.urls import path
from apps.agents import views

urlpatterns = [
    path("session/", views.create_session, name="agent-create-session"),
    path("message/", views.send_message, name="agent-send-message"),
    path("message/stream/", views.send_message_stream, name="agent-send-message-stream"),
    path("image/", views.upload_tongue_image, name="agent-upload-image"),
    path("session/<str:session_id>/", views.get_session, name="agent-get-session"),
    path("session/<str:session_id>/report/", views.get_report, name="agent-get-report"),
    path("session/<str:session_id>/delete/", views.delete_session, name="agent-delete-session"),
    path("safety-check/", views.safety_check, name="agent-safety-check"),
    # 个性化养生管理
    path("wellness/plan/", views.generate_wellness_plan, name="agent-wellness-plan"),
    path("wellness/checkin/", views.wellness_checkin, name="agent-wellness-checkin"),
    path("wellness/constitutions/", views.list_constitutions, name="agent-wellness-constitutions"),
    path("wellness/reports/", views.list_user_reports, name="agent-wellness-reports"),
]
