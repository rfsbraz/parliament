"""Add missing XIV Legislature interest registry fields

Revision ID: d0f14597c3d5
Revises: a13dc27193ca
Create Date: 2025-08-04 18:41:42.931637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0f14597c3d5'
down_revision: Union[str, Sequence[str], None] = 'a13dc27193ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing XIV Legislature interest registry fields."""
    
    # Looking at the unmapped fields, most are already handled by existing unified models.
    # The analysis shows all fields are covered by the current schema:
    # 
    # ✅ PositionEndDate, PositionBeginDate → Already in RegistoInteressesUnified (position_begin_date, position_end_date)
    # ✅ ServicesProvided → Already handled by RegistoInteressesApoioUnified with benefit_type='service'
    # ✅ Societies.Entity → Already in RegistoInteressesSociedadeUnified.entity field
    # ✅ Activities.Type → Already in RegistoInteressesAtividadeUnified.type_classification field
    # ✅ SocialPositions.Type → Already in RegistoInteressesSocialPositionUnified.type_classification field
    # ✅ GenDadosPessoais.Sexo → Already in RegistoInteressesUnified.gender field
    # ✅ GenServicoPrestado.Local → Already in RegistoInteressesApoioUnified.service_location field
    #
    # All unmapped fields from XIV Legislature are actually already covered by the unified model schema.
    # The STRICT MODE error indicates the mapper isn't recognizing these existing fields correctly.
    # The solution is to update the mappers to properly map these fields, not add new database fields.
    
    # No database schema changes needed - all fields already exist in unified models
    pass


def downgrade() -> None:
    """Downgrade schema.""" 
    # No schema changes were made
    pass
