import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import StudentRegistration, UserProfile, CollegeTeamMember

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Ensure each user has an associated UserProfile with the proper role.
    If the user's email matches an authorized CollegeTeamMember, automatically link them
    and ensure they have the 'university' partner role.
    """
    is_team_member = False
    if instance.email:
        team_entries = CollegeTeamMember.objects.filter(email__iexact=instance.email)
        if team_entries.exists():
            is_team_member = True
            team_entries.filter(user__isnull=True).update(user=instance)

    if created:
        if instance.is_superuser or instance.is_staff:
            role = 'admin'
        elif is_team_member:
            role = 'university'
        else:
            role = 'student'
        UserProfile.objects.get_or_create(user=instance, defaults={'role': role})
    else:
        if not hasattr(instance, 'profile'):
            if instance.is_superuser or instance.is_staff:
                role = 'admin'
            elif is_team_member:
                role = 'university'
            else:
                role = 'student'
            UserProfile.objects.get_or_create(user=instance, defaults={'role': role})
        elif is_team_member and instance.profile.role == 'student':
            instance.profile.role = 'university'
            instance.profile.save()


@receiver(post_save, sender=StudentRegistration)
def log_student_registration(sender, instance, created, **kwargs):
    """
    Signal receiver triggered after a StudentRegistration record is saved.
    Logs successful submissions and status updates.
    """
    if created:
        logger.info(
            f"[REGISTRATION CREATED] ID: {instance.registration_id} | "
            f"Student: {instance.full_name} | "
            f"College: {instance.college.name} | "
            f"Course: {instance.course.name} | "
            f"Status: {instance.status}"
        )
    else:
        logger.info(
            f"[REGISTRATION UPDATED] ID: {instance.registration_id} | Status: {instance.status}"
        )
