import requests
import json
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from projects.models import Project
from generation.models import Generations

import logging
logger = logging.getLogger(__name__)

class FeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        category = request.data.get('category', 'Other')
        rating = request.data.get('rating', 'ok')
        description = request.data.get('description', '')

        if not description:
            return Response({"error": "Description is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Limit description to 500 characters
        description = description[:500]

        # Fetch user details
        user = request.user
        
        # Get last generated UI details
        last_project = Project.objects.filter(user=user).order_by('-created_at').first()
        last_generation = None
        if last_project:
            last_generation = Generations.objects.filter(project=last_project, status='success').order_by('-created_at').first()

        project_name = last_project.title if last_project else "N/A"
        generation_id = str(last_generation.id) if last_generation else "N/A"
        
        # Format ratings with emojis for discord (matching frontend 1-5 scale)
        rating_map = {
            1: "😞 Poor",
            2: "😐 Fair",
            3: "🙂 Good",
            4: "� Great",
            5: "🤩 Loved it"
        }
        
        try:
            rating_int = int(rating)
            display_rating = rating_map.get(rating_int, f"Unknown ({rating})")
        except (ValueError, TypeError):
            display_rating = str(rating)

        # Build Discord Embed
        embed = {
            "title": f"New Feedback: {category}",
            "color": 3447003, # Blue
            "fields": [
                {"name": "Rating", "value": display_rating, "inline": True},
                {"name": "Category", "value": category, "inline": True},
                {"name": "User", "value": f"{user.name} ({user.email})", "inline": False},
                {"name": "User ID", "value": str(user.id), "inline": True},
                {"name": "Date/Time", "value": timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC"), "inline": True},
                {"name": "Description", "value": description, "inline": False},
                {"name": "Last Project", "value": project_name, "inline": True},
                {"name": "Generation ID", "value": generation_id, "inline": True}
            ],
            "footer": {
                "text": "DBurst Feedback System"
            }
        }

        webhook_url = getattr(settings, 'DISCORD_WEBHOOK', None)
        if not webhook_url:
            logger.error("DISCORD_WEBHOOK not configured in settings")
            return Response({"message": "Feedback recorded (Webhook not configured)"}, status=status.HTTP_200_OK)

        try:
            payload = {"embeds": [embed]}
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to send feedback to Discord: {str(e)}")
            return Response({"error": "Failed to send feedback to Discord"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Feedback sent successfully!"}, status=status.HTTP_200_OK)