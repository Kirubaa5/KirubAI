import csv
import io
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import asc, desc

from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.user import User
from schemas.export import (
    ExportFilterParams,
    ExportPreviewResponse,
    ExportJSONResponse,
    ExportVocabularyItem,
    ExportWordDetail,
    ExportExampleItem,
)


class ExportService:
    @staticmethod
    def _build_query(db: Session, user: User, filters: ExportFilterParams):
        """Construct isolated query applying all specified filters."""
        query = (
            db.query(Vocabulary)
            .options(
                joinedload(Vocabulary.details),
                selectinload(Vocabulary.examples),
            )
            .filter(Vocabulary.user_id == user.id)
        )

        now = datetime.now(timezone.utc)

        # 1. Status Filter
        if filters.status and filters.status.lower() != "all":
            status_lower = filters.status.lower().strip()
            if status_lower == "active":
                query = query.filter(
                    Vocabulary.status.in_(["learned", "practiced", "recalled", "reinforced"])
                )
            elif status_lower == "mastered":
                query = query.filter(Vocabulary.status == "mastered")
            elif status_lower == "struggling":
                query = query.filter(Vocabulary.status == "struggling")
            elif status_lower in ["due", "due_for_review"]:
                query = query.filter(
                    Vocabulary.next_review_at.isnot(None),
                    Vocabulary.next_review_at <= now,
                )
            else:
                query = query.filter(Vocabulary.status == status_lower)

        # 2. CEFR Level Filter
        if filters.cefr_level and filters.cefr_level.lower() != "all":
            cefr_clean = filters.cefr_level.strip().upper()
            query = query.join(Vocabulary.details).filter(WordDetails.cefr_level == cefr_clean)

        # 3. Mastery Score Bounds
        if filters.min_mastery is not None:
            query = query.filter(Vocabulary.mastery_score >= filters.min_mastery)
        if filters.max_mastery is not None:
            query = query.filter(Vocabulary.mastery_score <= filters.max_mastery)

        # 4. Date Range
        if filters.date_from is not None:
            query = query.filter(Vocabulary.created_at >= filters.date_from)
        if filters.date_to is not None:
            query = query.filter(Vocabulary.created_at <= filters.date_to)

        # 5. Sorting (deterministic with ID fallback)
        sort_map = {
            "word": Vocabulary.word,
            "created_at": Vocabulary.created_at,
            "mastery_score": Vocabulary.mastery_score,
            "status": Vocabulary.status,
            "last_reviewed_at": Vocabulary.last_reviewed_at,
        }
        sort_col = sort_map.get(filters.sort_by.lower(), Vocabulary.word)
        if filters.order.lower() == "desc":
            query = query.order_by(desc(sort_col), asc(Vocabulary.id))
        else:
            query = query.order_by(asc(sort_col), asc(Vocabulary.id))

        return query

    @classmethod
    def get_export_data(
        cls, db: Session, user: User, filters: ExportFilterParams
    ) -> List[Vocabulary]:
        """Fetch all vocabulary items matching filter criteria for the user."""
        query = cls._build_query(db, user, filters)
        return query.all()

    @classmethod
    def get_preview(
        cls, db: Session, user: User, filters: ExportFilterParams
    ) -> ExportPreviewResponse:
        """Get summary metrics and preview of matching vocabulary for export."""
        # Total words for this user
        total_count = db.query(Vocabulary).filter(Vocabulary.user_id == user.id).count()

        # Matching items
        matching_items = cls.get_export_data(db, user, filters)
        matching_count = len(matching_items)

        # Status distribution
        status_dist: Dict[str, int] = {}
        cefr_dist: Dict[str, int] = {}
        sample_words: List[str] = []

        for item in matching_items:
            # Status
            st = item.status or "unknown"
            status_dist[st] = status_dist.get(st, 0) + 1

            # CEFR
            cefr = (item.details.cefr_level if item.details and item.details.cefr_level else "Unranked").upper()
            cefr_dist[cefr] = cefr_dist.get(cefr, 0) + 1

            # Sample words (up to 10)
            if len(sample_words) < 10:
                sample_words.append(item.word)

        return ExportPreviewResponse(
            total_vocabulary_count=total_count,
            matching_words_count=matching_count,
            status_distribution=status_dist,
            cefr_distribution=cefr_dist,
            sample_words=sample_words,
        )

    @staticmethod
    def generate_csv(
        vocabularies: List[Vocabulary],
        include_examples: bool = True,
        include_learning_stats: bool = True,
    ) -> str:
        """Generate formatted CSV string with UTF-8 support and clean column headers."""
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # Header columns
        headers = [
            "Word",
            "Part of Speech",
            "CEFR Level",
            "Simple Meaning",
            "Contextual Meaning",
            "Pronunciation",
            "Synonyms",
            "Antonyms",
            "Word Forms",
            "Collocations",
        ]
        if include_examples:
            headers.append("Examples")
        if include_learning_stats:
            headers.extend([
                "Status",
                "Mastery Score",
                "Practice Count",
                "Successful Usage Count",
                "Failed Recall Count",
                "Review Interval (Days)",
                "Next Review At",
                "Last Practiced At",
                "Last Reviewed At",
                "Added At",
            ])

        writer.writerow(headers)

        for vocab in vocabularies:
            details = vocab.details
            pos = (details.part_of_speech if details and details.part_of_speech else "")
            cefr = (details.cefr_level if details and details.cefr_level else "")
            simple_meaning = (details.simple_meaning if details and details.simple_meaning else "")
            contextual_meaning = (details.contextual_meaning if details and details.contextual_meaning else "")
            pronunciation = (details.pronunciation_text if details and details.pronunciation_text else "")

            # Lists handling
            synonyms_str = "; ".join(details.synonyms) if details and details.synonyms else ""
            antonyms_str = "; ".join(details.antonyms) if details and details.antonyms else ""
            collocations_str = "; ".join(details.collocations) if details and details.collocations else ""

            # Word forms
            forms_str = ""
            if details and details.word_forms and isinstance(details.word_forms, dict):
                forms_str = " | ".join(f"{k}: {v}" for k, v in sorted(details.word_forms.items()) if v)

            row = [
                vocab.word,
                pos,
                cefr,
                simple_meaning,
                contextual_meaning,
                pronunciation,
                synonyms_str,
                antonyms_str,
                forms_str,
                collocations_str,
            ]

            if include_examples:
                examples_list = []
                if vocab.examples:
                    sorted_examples = sorted(vocab.examples, key=lambda x: x.order_index)
                    for idx, ex in enumerate(sorted_examples, start=1):
                        ctx = f" [{ex.context_label}]" if ex.context_label else ""
                        examples_list.append(f"{idx}. {ex.example_text}{ctx}")
                row.append(" | ".join(examples_list))

            if include_learning_stats:
                mastery_pct = f"{round(vocab.mastery_score * 100)}%"
                next_review = vocab.next_review_at.isoformat() if vocab.next_review_at else ""
                last_practiced = vocab.last_practiced_at.isoformat() if vocab.last_practiced_at else ""
                last_reviewed = vocab.last_reviewed_at.isoformat() if vocab.last_reviewed_at else ""
                created_at = vocab.created_at.isoformat() if vocab.created_at else ""

                row.extend([
                    vocab.status or "new",
                    mastery_pct,
                    str(vocab.practice_count),
                    str(vocab.successful_usage_count),
                    str(vocab.failed_recall_count),
                    str(vocab.review_interval_days),
                    next_review,
                    last_practiced,
                    last_reviewed,
                    created_at,
                ])

            writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def generate_anki(
        vocabularies: List[Vocabulary],
        format_type: str = "tsv",
        include_examples: bool = True,
    ) -> str:
        """
        Generate Anki-compatible export file.
        Uses TSV (Tab Separated Values) format with standard Anki import headers:
        #separator:tab
        #html:true
        #tags column:6
        """
        output = io.StringIO()

        if format_type.lower() in ["tsv", "tab", "anki_tsv", "anki"]:
            output.write("#separator:tab\n")
            output.write("#html:true\n")
            output.write("#tags column:6\n")

            for vocab in vocabularies:
                details = vocab.details
                pos = (details.part_of_speech if details and details.part_of_speech else "word")
                cefr = (details.cefr_level if details and details.cefr_level else "B1")
                pronunciation = (details.pronunciation_text if details and details.pronunciation_text else "")
                simple_meaning = (details.simple_meaning if details and details.simple_meaning else "")
                contextual_meaning = (details.contextual_meaning if details and details.contextual_meaning else "")

                # 1. Front Card
                pron_html = f' <span style="color: #64748b; font-size: 13px;">{pronunciation}</span>' if pronunciation else ""
                front = (
                    f'<div style="font-size: 22px; font-weight: 700; color: #1d4ed8; text-align: center;">{vocab.word}</div>'
                    f'<div style="font-size: 13px; color: #475569; text-align: center; margin-top: 4px;">'
                    f'<i>{pos}</i> &bull; <span style="font-weight: 600; color: #0284c7;">{cefr}</span>{pron_html}'
                    f'</div>'
                )

                # 2. Back Card
                back_sections = []
                back_sections.append(
                    f'<div style="margin-bottom: 8px; font-size: 15px;"><strong>Meaning:</strong> {simple_meaning}</div>'
                )

                if contextual_meaning and contextual_meaning != simple_meaning:
                    back_sections.append(
                        f'<div style="margin-bottom: 8px; font-size: 14px; color: #334155;"><strong>Context:</strong> {contextual_meaning}</div>'
                    )

                # Word Forms
                if details and details.word_forms and isinstance(details.word_forms, dict):
                    valid_forms = [f"<b>{k}:</b> {v}" for k, v in sorted(details.word_forms.items()) if v]
                    if valid_forms:
                        back_sections.append(
                            f'<div style="margin-bottom: 8px; font-size: 13px; color: #475569;"><strong>Forms:</strong> {", ".join(valid_forms)}</div>'
                        )

                # Collocations
                if details and details.collocations:
                    colls = ", ".join(details.collocations[:4])
                    back_sections.append(
                        f'<div style="margin-bottom: 8px; font-size: 13px; color: #0f766e;"><strong>Collocations:</strong> {colls}</div>'
                    )

                # Examples
                if include_examples and vocab.examples:
                    ex_items = []
                    sorted_examples = sorted(vocab.examples, key=lambda x: x.order_index)
                    for ex in sorted_examples[:3]:
                        ctx_badge = f' <span style="font-size: 11px; color: #64748b;">({ex.context_label})</span>' if ex.context_label else ""
                        ex_items.append(f'<li style="margin-bottom: 3px;">{ex.example_text}{ctx_badge}</li>')
                    if ex_items:
                        back_sections.append(
                            f'<div style="margin-top: 8px;"><strong style="font-size: 13px;">Examples:</strong><ul style="margin: 4px 0 0 18px; padding: 0; font-size: 13px;">{"".join(ex_items)}</ul></div>'
                        )

                back = f'<div style="text-align: left; line-height: 1.5;">{"".join(back_sections)}</div>'

                # 3. Part of speech
                pos_field = pos
                # 4. CEFR Level
                cefr_field = cefr
                # 5. Status & Mastery
                mastery_field = f"{vocab.status} ({round(vocab.mastery_score * 100)}%)"
                # 6. Tags (space-separated for Anki)
                tags_field = f"KirubAI CEFR_{cefr} Status_{vocab.status}"

                # Escape tabs and newlines within fields to keep TSV integrity
                def sanitize_tsv(val: str) -> str:
                    return val.replace("\t", " ").replace("\r\n", " ").replace("\n", " ")

                tsv_line = "\t".join([
                    sanitize_tsv(front),
                    sanitize_tsv(back),
                    sanitize_tsv(pos_field),
                    sanitize_tsv(cefr_field),
                    sanitize_tsv(mastery_field),
                    sanitize_tsv(tags_field),
                ])
                output.write(tsv_line + "\n")

        else:
            # Anki CSV format
            writer = csv.writer(output, quoting=csv.QUOTE_ALL)
            writer.writerow(["Front", "Back", "Part of Speech", "CEFR Level", "Status", "Tags"])
            for vocab in vocabularies:
                details = vocab.details
                pos = (details.part_of_speech if details and details.part_of_speech else "")
                cefr = (details.cefr_level if details and details.cefr_level else "B1")
                simple_meaning = (details.simple_meaning if details and details.simple_meaning else "")
                front = vocab.word
                back = f"{simple_meaning}"
                tags = f"KirubAI CEFR_{cefr} Status_{vocab.status}"
                writer.writerow([front, back, pos, cefr, vocab.status, tags])

        return output.getvalue()

    @classmethod
    def generate_json_dict(
        cls,
        vocabularies: List[Vocabulary],
        user: User,
        filters: ExportFilterParams,
    ) -> Dict[str, Any]:
        """Generate structured dictionary representing full export archive."""
        vocab_items: List[Dict[str, Any]] = []

        for v in vocabularies:
            details_dict = None
            if v.details:
                details_dict = {
                    "simple_meaning": v.details.simple_meaning,
                    "contextual_meaning": v.details.contextual_meaning,
                    "part_of_speech": v.details.part_of_speech,
                    "pronunciation_text": v.details.pronunciation_text,
                    "cefr_level": v.details.cefr_level,
                    "difficulty_score": v.details.difficulty_score,
                    "synonyms": v.details.synonyms or [],
                    "antonyms": v.details.antonyms or [],
                    "word_forms": v.details.word_forms or {},
                    "collocations": v.details.collocations or [],
                }

            examples_list = []
            if v.examples:
                sorted_ex = sorted(v.examples, key=lambda x: x.order_index)
                for ex in sorted_ex:
                    examples_list.append({
                        "example_text": ex.example_text,
                        "context_label": ex.context_label,
                        "order_index": ex.order_index,
                    })

            vocab_items.append({
                "id": v.id,
                "word": v.word,
                "status": v.status,
                "mastery_score": v.mastery_score,
                "practice_count": v.practice_count,
                "successful_usage_count": v.successful_usage_count,
                "failed_recall_count": v.failed_recall_count,
                "review_interval_days": v.review_interval_days,
                "next_review_at": v.next_review_at.isoformat() if v.next_review_at else None,
                "last_practiced_at": v.last_practiced_at.isoformat() if v.last_practiced_at else None,
                "last_reviewed_at": v.last_reviewed_at.isoformat() if v.last_reviewed_at else None,
                "created_at": v.created_at.isoformat() if v.created_at else None,
                "updated_at": v.updated_at.isoformat() if v.updated_at else None,
                "details": details_dict,
                "examples": examples_list,
            })

        return {
            "app": "KirubAI",
            "version": "0.1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user_email": user.email,
            "total_words": len(vocab_items),
            "filters_applied": {
                "status": filters.status,
                "cefr_level": filters.cefr_level,
                "min_mastery": filters.min_mastery,
                "max_mastery": filters.max_mastery,
                "sort_by": filters.sort_by,
                "order": filters.order,
            },
            "vocabulary": vocab_items,
        }
