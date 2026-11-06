
import asyncio
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.database import AsyncSessionLocal
from db.models.product import Product
from db.models.category import Category
from db.models.product_attribute import ProductAttribute


BACKEND_DIR = Path(__file__).resolve().parent.parent

FINE_TUNED_MODEL_PATH = (
    BACKEND_DIR
    / "ml"
    / "semantic_search"
    / "models"
    / "best_model"
)

EXPECTED_DIMENSION = 384
BATCH_SIZE = 32


def load_model():
    # Do not silently fall back to the original model.
    if not FINE_TUNED_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Fine-tuned model not found: {FINE_TUNED_MODEL_PATH}"
        )

    if not (FINE_TUNED_MODEL_PATH / "config.json").exists():
        raise FileNotFoundError(
            "Fine-tuned model config.json is missing."
        )

    print(f"Loading fine-tuned model: {FINE_TUNED_MODEL_PATH}")

    model = SentenceTransformer(str(FINE_TUNED_MODEL_PATH))

    dimension = model.get_sentence_embedding_dimension()

    print(f"Model embedding dimension: {dimension}")

    if dimension != EXPECTED_DIMENSION:
        raise ValueError(
            f"Expected {EXPECTED_DIMENSION}-dimensional embeddings, "
            f"but model produces {dimension}."
        )

    return model


def build_embedding_text(product, category_name):
    attribute_names = sorted(
        mapping.attribute.name
        for mapping in product.product_attributes
        if mapping.attribute is not None
    )

    attributes_text = (
        ", ".join(attribute_names)
        if attribute_names
        else "None"
    )

    return (
        f"Product: {product.name}. "
        f"Description: {product.description or 'Not specified'}. "
        f"Category: {category_name or 'Uncategorized'}. "
        f"Attributes: {attributes_text}."
    )


async def generate_product_embeddings():
    model = load_model()

    async with AsyncSessionLocal() as session:

        # The transaction automatically rolls back if any error occurs.
        async with session.begin():

            result = await session.execute(
                select(
                    Product,
                    Category.name.label("category_name"),
                )
                .outerjoin(
                    Category,
                    Product.category_id == Category.id,
                )
                .options(
                    selectinload(
                        Product.product_attributes
                    ).selectinload(
                        ProductAttribute.attribute
                    )
                )
                .order_by(Product.id)
            )

            products = result.all()

            if not products:
                print("No products found.")
                return

            print(f"\nFound {len(products)} products.")
            print("Generating fine-tuned embeddings...\n")

            updated_count = 0

            for start in range(0, len(products), BATCH_SIZE):

                batch = products[start:start + BATCH_SIZE]

                texts = [
                    build_embedding_text(product, category_name)
                    for product, category_name in batch
                ]

                embeddings = model.encode(
                    texts,
                    batch_size=BATCH_SIZE,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )

                # Validate the entire batch before assigning it.
                if embeddings.shape != (
                    len(batch),
                    EXPECTED_DIMENSION,
                ):
                    raise ValueError(
                        f"Unexpected embedding shape: {embeddings.shape}"
                    )

                if not np.isfinite(embeddings).all():
                    raise ValueError(
                        "Invalid NaN or infinite values in embeddings."
                    )

                for (product, _), embedding in zip(batch, embeddings):

                    vector = embedding.tolist()

                    if len(vector) != EXPECTED_DIMENSION:
                        raise ValueError(
                            f"Invalid dimension for product {product.id}"
                        )

                    product.embedding = vector

                updated_count += len(batch)

                print(
                    f"Prepared {updated_count}/{len(products)} embeddings."
                )

            # Commit happens automatically when session.begin() exits.
            print("\nAll embeddings validated.")
            print("Database transaction will now commit.")

        print(
            f"\nSuccessfully regenerated {updated_count} product embeddings."
        )


if __name__ == "__main__":
    asyncio.run(generate_product_embeddings())
