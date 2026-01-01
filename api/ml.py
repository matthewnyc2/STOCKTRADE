"""
ML API router.

Endpoints for machine learning model management and training.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from database.connection import get_db_context
from database.models import MLModelModel
from models import (
    MLModel,
    ModelStatus,
    ModelType,
    PredictionRequest,
    TrainingProgressResponse,
    TrainingRequest,
)
from services.ml_factory import (
    FeatureEngine,
    MLFactory,
    PredictionResult,
    TrainingConfig,
    get_ml_factory,
)


router = APIRouter(prefix="/ml", tags=["ml"])


@router.get("/models", response_model=list[MLModel])
async def list_ml_models(
    model_type: ModelType | None = None,
    status_filter: str | None = None,
    limit: int = 50,
) -> list[MLModel]:
    """
    List ML models with optional filtering.

    Args:
        model_type: Filter by model type.
        status_filter: Filter by model status.
        limit: Maximum number of results.

    Returns:
        List[MLModel]: List of ML models.
    """
    with get_db_context() as session:
        query = session.query(MLModelModel)

        if model_type:
            query = query.filter(MLModelModel.model_type == model_type.value)

        if status_filter:
            query = query.filter(MLModelModel.status == status_filter)

        models = query.order_by(MLModelModel.created_at.desc()).limit(limit).all()

        return [_db_to_pydantic(m) for m in models]


@router.get("/models/{model_id}", response_model=MLModel)
async def get_ml_model(model_id: str) -> MLModel:
    """
    Get a specific ML model by ID.

    Args:
        model_id: The model ID.

    Returns:
        MLModel: The requested model.

    Raises:
        HTTPException: If model not found.
    """
    with get_db_context() as session:
        model = session.query(MLModelModel).filter(
            MLModelModel.id == model_id
        ).first()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found",
            )

        return _db_to_pydantic(model)


@router.post("/train", response_model=dict[str, str])
async def start_training(request: TrainingRequest) -> dict[str, str]:
    """
    Start training a new ML model.

    Args:
        request: Training configuration

    Returns:
        Dict with task_id for progress tracking

    Raises:
        HTTPException: If training fails to start
    """
    try:
        # Get ML Factory
        ml_factory = get_ml_factory()

        # Create training config
        config = TrainingConfig(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            timeframe=request.timeframe,
            model_type=request.model_type,
            sequence_length=request.sequence_length,
            prediction_horizon=request.prediction_horizon,
            train_split=request.train_split,
            batch_size=request.batch_size,
            epochs=request.epochs,
            learning_rate=request.learning_rate,
            early_stopping_patience=request.early_stopping_patience,
            feature_selection=request.feature_selection,
            target_type=request.target_type,
            threshold=request.threshold,
        )

        # Start training
        task_id = ml_factory.train_model(config)

        return {
            "task_id": task_id,
            "status": "started",
            "message": "Training started successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start training: {str(e)}",
        )


@router.get("/training/{task_id}", response_model=TrainingProgressResponse)
async def get_training_progress(task_id: str) -> TrainingProgressResponse:
    """
    Get training progress for a task.

    Args:
        task_id: Training task ID

    Returns:
        Training progress information

    Raises:
        HTTPException: If task not found
    """
    ml_factory = get_ml_factory()
    progress = ml_factory.get_training_progress(task_id)

    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training task {task_id} not found",
        )

    return TrainingProgressResponse(**progress)


@router.post("/models/{model_id}/predict")
async def generate_prediction(model_id: str, request: PredictionRequest) -> dict[str, Any]:
    """
    Generate a prediction using a trained model.

    Args:
        model_id: The model ID
        request: Prediction request with symbol and lookback periods

    Returns:
        Prediction result

    Raises:
        HTTPException: If model not found or prediction fails
    """
    try:
        ml_factory = get_ml_factory()

        # Load recent price data
        with get_db_context() as session:
            from database.models import PriceModel

            prices = session.query(PriceModel).filter(
                PriceModel.symbol == request.symbol,
            ).order_by(PriceModel.timestamp.desc()).limit(request.lookback_periods).all()

            if not prices:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No price data found for {request.symbol}",
                )

            # Convert to ML factory format
            current_data = [
                {
                    "symbol": p.symbol,
                    "timestamp": p.timestamp,
                    "open": float(p.open),
                    "high": float(p.high),
                    "low": float(p.low),
                    "close": float(p.close),
                    "volume": float(p.volume),
                }
                for p in reversed(prices)
            ]

        # Generate predictions
        predictions = ml_factory.generate_predictions(model_id, current_data)

        return {
            "predictions": [p.to_dict() for p in predictions],
            "model_id": model_id,
            "symbol": request.symbol,
            "timestamp": predictions[0].timestamp.isoformat() if predictions else None,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


@router.post("/models/{model_id}/deploy", response_model=MLModel)
async def deploy_model(model_id: str) -> MLModel:
    """
    Deploy an ML model for signal generation.

    Args:
        model_id: The model ID.

    Returns:
        MLModel: The deployed model.

    Raises:
        HTTPException: If model not found or not ready.
    """
    with get_db_context() as session:
        model = session.query(MLModelModel).filter(
            MLModelModel.id == model_id
        ).first()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found",
            )

        if model.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model {model_id} is not ready. Current status: {model.status}",
            )

        # Deploy model
        model.is_deployed = True
        model.deployed_at = datetime.utcnow()
        model.status = "deployed"
        session.commit()
        session.refresh(model)

        return _db_to_pydantic(model)


@router.post("/models/{model_id}/undeploy", response_model=MLModel)
async def undeploy_model(model_id: str) -> MLModel:
    """
    Undeploy an ML model.

    Args:
        model_id: The model ID.

    Returns:
        MLModel: The undeployed model.

    Raises:
        HTTPException: If model not found.
    """
    with get_db_context() as session:
        model = session.query(MLModelModel).filter(
            MLModelModel.id == model_id
        ).first()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found",
            )

        # Undeploy model
        model.is_deployed = False
        model.deployed_at = None
        model.status = "ready"
        session.commit()
        session.refresh(model)

        return _db_to_pydantic(model)


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ml_model(model_id: str) -> None:
    """
    Delete an ML model.

    Args:
        model_id: The model ID.

    Raises:
        HTTPException: If model not found.
    """
    with get_db_context() as session:
        model = session.query(MLModelModel).filter(
            MLModelModel.id == model_id
        ).first()

        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model {model_id} not found",
            )

        session.delete(model)
        session.commit()


@router.get("/features")
async def list_features() -> dict[str, list[str]]:
    """
    Get list of all available features and feature groups.

    Returns:
        Dictionary of feature groups
    """
    engine = FeatureEngine()
    return {
        "all_features": engine.get_all_features(),
        "feature_groups": engine.get_feature_groups(),
    }


@router.get("/models/{model_id}/info")
async def get_model_info(model_id: str) -> dict[str, Any]:
    """
    Get detailed information about a model including metadata.

    Args:
        model_id: The model ID

    Returns:
        Model information

    Raises:
        HTTPException: If model not found
    """
    ml_factory = get_ml_factory()
    info = ml_factory.get_model_info(model_id)

    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found",
        )

    return info


def _db_to_pydantic(db_model: MLModelModel) -> MLModel:
    """Convert SQLAlchemy model to Pydantic model."""
    return MLModel(
        id=db_model.id,
        name=db_model.name,
        model_type=ModelType(db_model.model_type),
        features=db_model.features or [],
        training_start=db_model.training_start,
        training_end=db_model.training_end,
        accuracy=float(db_model.accuracy) if db_model.accuracy else None,
        created_at=db_model.created_at,
        status=ModelStatus(db_model.status),
        parameters=db_model.parameters or {},
        metrics=db_model.metrics or {},
        symbols=getattr(db_model, "symbols", None),
        timeframe=getattr(db_model, "timeframe", None),
        sequence_length=getattr(db_model, "sequence_length", None),
        prediction_horizon=getattr(db_model, "prediction_horizon", None),
        target_type=getattr(db_model, "target_type", None),
        model_path=getattr(db_model, "model_path", None),
        is_deployed=getattr(db_model, "is_deployed", False),
        deployed_at=getattr(db_model, "deployed_at", None),
    )
