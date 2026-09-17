import json
from datetime import datetime, timezone
from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from middleware.auth import get_current_user
from schemas.export import ExportFilterParams, ExportPreviewResponse, ExportJSONResponse
from services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["Export & Data Portability"])


def _generate_filename(prefix: str, ext: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"kirubai_{prefix}_{timestamp}.{ext}"


@router.get("/preview", response_model=ExportPreviewResponse)
async def get_export_preview(
    status: Optional[str] = Query(default="all", description="Vocabulary status filter"),
    cefr_level: Optional[str] = Query(default=None, description="CEFR level filter"),
    min_mastery: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Minimum mastery score"),
    max_mastery: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Maximum mastery score"),
    date_from: Optional[datetime] = Query(default=None, description="Start created date"),
    date_to: Optional[datetime] = Query(default=None, description="End created date"),
    sort_by: str = Query(default="word", description="Sort by field"),
    order: str = Query(default="asc", description="Sort direction"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return summary preview and statistics of vocabulary matching export filters."""
    filters = ExportFilterParams(
        status=status,
        cefr_level=cefr_level,
        min_mastery=min_mastery,
        max_mastery=max_mastery,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        order=order,
    )
    return ExportService.get_preview(db, current_user, filters)


@router.get("/csv")
async def export_csv(
    status: Optional[str] = Query(default="all"),
    cefr_level: Optional[str] = Query(default=None),
    min_mastery: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    max_mastery: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    sort_by: str = Query(default="word"),
    order: str = Query(default="asc"),
    include_examples: bool = Query(default=True),
    include_learning_stats: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export vocabulary and learning history as a standard UTF-8 CSV spreadsheet."""
    filters = ExportFilterParams(
        format="csv",
        status=status,
        cefr_level=cefr_level,
        min_mastery=min_mastery,
        max_mastery=max_mastery,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        order=order,
        include_examples=include_examples,
        include_learning_stats=include_learning_stats,
    )

    items = ExportService.get_export_data(db, current_user, filters)
    csv_text = ExportService.generate_csv(
        items,
        include_examples=include_examples,
        include_learning_stats=include_learning_stats,
    )

    filename = _generate_filename("vocabulary", "csv")
    # Encode with utf-8-sig (UTF-8 with BOM) for seamless compatibility with Microsoft Excel & Google Sheets
    content_bytes = csv_text.encode("utf-8-sig")

    return Response(
        content=content_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@router.get("/anki")
async def export_anki(
    status: Optional[str] = Query(default="all"),
    cefr_level: Optional[str] = Query(default=None),
    min_mastery: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    max_mastery: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    sort_by: str = Query(default="word"),
    order: str = Query(default="asc"),
    format_type: Literal["tsv", "csv"] = Query(default="tsv", description="Anki file format"),
    include_examples: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export vocabulary as an Anki-compatible study deck (TSV/TXT or CSV)."""
    filters = ExportFilterParams(
        format="anki_tsv" if format_type == "tsv" else "anki_csv",
        status=status,
        cefr_level=cefr_level,
        min_mastery=min_mastery,
        max_mastery=max_mastery,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        order=order,
        include_examples=include_examples,
    )

    items = ExportService.get_export_data(db, current_user, filters)
    anki_text = ExportService.generate_anki(
        items, format_type=format_type, include_examples=include_examples
    )

    ext = "txt" if format_type == "tsv" else "csv"
    filename = _generate_filename("anki_deck", ext)
    content_bytes = anki_text.encode("utf-8")

    return Response(
        content=content_bytes,
        media_type="text/tab-separated-values; charset=utf-8" if format_type == "tsv" else "text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@router.get("/json")
async def export_json(
    status: Optional[str] = Query(default="all"),
    cefr_level: Optional[str] = Query(default=None),
    min_mastery: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    max_mastery: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    sort_by: str = Query(default="word"),
    order: str = Query(default="asc"),
    download: bool = Query(default=True, description="Return as attachment download"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export complete vocabulary archive and learning metrics in JSON format."""
    filters = ExportFilterParams(
        format="json",
        status=status,
        cefr_level=cefr_level,
        min_mastery=min_mastery,
        max_mastery=max_mastery,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        order=order,
    )

    items = ExportService.get_export_data(db, current_user, filters)
    json_data = ExportService.generate_json_dict(items, current_user, filters)
    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

    if download:
        filename = _generate_filename("vocabulary_archive", "json")
        return Response(
            content=json_str.encode("utf-8"),
            media_type="application/json; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
            },
        )
    return json_data


@router.get("")
async def export_all(
    format: Literal["csv", "anki", "anki_tsv", "anki_csv", "json"] = Query(default="csv"),
    status: Optional[str] = Query(default="all"),
    cefr_level: Optional[str] = Query(default=None),
    min_mastery: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    max_mastery: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    sort_by: str = Query(default="word"),
    order: str = Query(default="asc"),
    include_examples: bool = Query(default=True),
    include_learning_stats: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unified export dispatcher supporting format parameter."""
    if format in ["anki", "anki_tsv"]:
        return await export_anki(
            status=status,
            cefr_level=cefr_level,
            min_mastery=min_mastery,
            max_mastery=max_mastery,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            order=order,
            format_type="tsv",
            include_examples=include_examples,
            current_user=current_user,
            db=db,
        )
    elif format == "anki_csv":
        return await export_anki(
            status=status,
            cefr_level=cefr_level,
            min_mastery=min_mastery,
            max_mastery=max_mastery,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            order=order,
            format_type="csv",
            include_examples=include_examples,
            current_user=current_user,
            db=db,
        )
    elif format == "json":
        return await export_json(
            status=status,
            cefr_level=cefr_level,
            min_mastery=min_mastery,
            max_mastery=max_mastery,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            order=order,
            download=True,
            current_user=current_user,
            db=db,
        )
    else:
        return await export_csv(
            status=status,
            cefr_level=cefr_level,
            min_mastery=min_mastery,
            max_mastery=max_mastery,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            order=order,
            include_examples=include_examples,
            include_learning_stats=include_learning_stats,
            current_user=current_user,
            db=db,
        )
