from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.models import (
    Base,
    Recommendation,
    RecommendationEvidence,
    RecommendationFeedback,
    SourceConfig,
)


def make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()


def seed_recommendation(db):
    recommendation = Recommendation(
        symbol="AAPL",
        recommendation_date=datetime(2025, 6, 24),
        setup_type="breakout",
        entry_low=100.0,
        entry_high=102.0,
        stop_loss=96.0,
        target=108.0,
        mqs_score=87.5,
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation


def test_recommendation_evidence_persists_and_links_to_recommendation():
    db = make_db()
    recommendation = seed_recommendation(db)

    evidence = RecommendationEvidence(
        recommendation_id=recommendation.id,
        rule_name="RSI",
        rule_value="67",
        rule_threshold="60-75",
        passed=True,
    )
    db.add(evidence)
    db.commit()

    loaded = db.query(Recommendation).filter(Recommendation.id == recommendation.id).one()

    assert len(loaded.evidence) == 1
    assert loaded.evidence[0].rule_name == "RSI"
    assert loaded.evidence[0].rule_value == "67"
    assert loaded.evidence[0].rule_threshold == "60-75"
    assert loaded.evidence[0].passed is True
    assert loaded.evidence[0].recommendation_id == recommendation.id
    assert loaded.evidence[0].recommendation.id == recommendation.id


def test_recommendation_feedback_persists_and_links_to_recommendation():
    db = make_db()
    recommendation = seed_recommendation(db)

    feedback = RecommendationFeedback(
        recommendation_id=recommendation.id,
        helpful=True,
        rating=5,
        comment="Clear and actionable.",
    )
    db.add(feedback)
    db.commit()

    loaded = db.query(Recommendation).filter(Recommendation.id == recommendation.id).one()

    assert len(loaded.feedback) == 1
    assert loaded.feedback[0].helpful is True
    assert loaded.feedback[0].rating == 5
    assert loaded.feedback[0].comment == "Clear and actionable."
    assert loaded.feedback[0].recommendation_id == recommendation.id
    assert loaded.feedback[0].recommendation.id == recommendation.id


def test_source_config_can_be_created_and_queried():
    db = make_db()

    config = SourceConfig(
        name="Yahoo Finance",
        provider_type="yahoo",
        base_url="https://query1.finance.yahoo.com",
        api_key_ref=None,
        rate_limit=100,
    )
    db.add(config)
    db.commit()

    loaded = db.query(SourceConfig).filter(SourceConfig.provider_type == "yahoo").one()

    assert loaded.name == "Yahoo Finance"
    assert loaded.provider_type == "yahoo"
    assert loaded.enabled is True
    assert loaded.priority == 1
    assert loaded.base_url == "https://query1.finance.yahoo.com"
    assert loaded.rate_limit == 100


def test_recommendation_relationships_support_multiple_children():
    db = make_db()
    recommendation = seed_recommendation(db)

    db.add_all(
        [
            RecommendationEvidence(
                recommendation_id=recommendation.id,
                rule_name="ADX",
                rule_value="31",
                rule_threshold=">25",
                passed=True,
            ),
            RecommendationEvidence(
                recommendation_id=recommendation.id,
                rule_name="EMA_ALIGNMENT",
                rule_value="true",
                rule_threshold="EMA50 > EMA200",
                passed=True,
            ),
            RecommendationFeedback(
                recommendation_id=recommendation.id,
                helpful=False,
                rating=None,
                comment="Too late for my risk tolerance.",
            ),
        ]
    )
    db.commit()

    loaded = db.query(Recommendation).filter(Recommendation.id == recommendation.id).one()

    assert [item.rule_name for item in loaded.evidence] == ["ADX", "EMA_ALIGNMENT"]
    assert [item.helpful for item in loaded.feedback] == [False]
