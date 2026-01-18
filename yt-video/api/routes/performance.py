"""
Performance API Routes
Zamanlamalar ve istatistikler için endpoint'ler
"""
from fastapi import APIRouter
from utils.timing import get_summary, get_project_stats, clear_log

router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("/summary")
async def performance_summary():
    """
    Genel performance özeti

    Returns:
        Tüm operasyonların istatistikleri (ortalama, min, max, count)
    """
    summary = get_summary()
    return {
        "success": True,
        "summary": summary
    }


@router.get("/project/{project_id}")
async def project_performance(project_id: str):
    """
    Proje bazlı detaylı performance raporu

    Args:
        project_id: Proje ID'si

    Returns:
        Projeye ait sahne bazlı detaylı istatistikler
    """
    stats = get_project_stats(project_id)
    return {
        "success": True,
        "projectId": project_id,
        "stats": stats
    }


@router.get("/projects")
async def all_projects_performance():
    """
    Tüm projelerin performance istatistikleri

    Returns:
        Tüm projelerin listesi ve detayları
    """
    stats = get_project_stats()
    return {
        "success": True,
        "stats": stats
    }


@router.post("/clear")
async def clear_performance_log():
    """
    Performance loglarını temizle

    Returns:
        Başarı mesajı
    """
    clear_log()
    return {
        "success": True,
        "message": "Performance logs cleared"
    }
