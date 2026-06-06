"""Pydantic schemas for request validation."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class PredictRequest(BaseModel):
    """Validation schema for ESG prediction input."""

    primary_industry: Optional[str] = Field(default="Technology", description="Primary industry classification")
    log_market_cap: Optional[float] = Field(default=None, ge=0, le=100, description="Log market cap")
    log_employees: Optional[float] = Field(default=None, ge=0, le=100, description="Log employees")
    log_revenue_wins: Optional[float] = Field(default=None, ge=0, le=100, description="Log revenue wins")
    log_scope_1: Optional[float] = Field(default=None, ge=0, le=100, description="Log scope 1")
    log_scope_2: Optional[float] = Field(default=None, ge=0, le=100, description="Log scope 2")
    log_scope_3: Optional[float] = Field(default=None, ge=0, le=100, description="Log scope 3")
    log_energy_consumption: Optional[float] = Field(default=None, ge=0, le=100, description="Log energy consumption")
    log_waste_production: Optional[float] = Field(default=None, ge=0, le=100, description="Log waste production")
    log_water_consumption: Optional[float] = Field(default=None, ge=0, le=100, description="Log water consumption")
    log_hours_of_training_wins: Optional[float] = Field(default=None, ge=0, le=100, description="Log hours of training wins")
    log_ceo_compensation: Optional[float] = Field(default=None, ge=0, le=100, description="Log CEO compensation")
    independent_board_members_percentage: Optional[float] = Field(default=None, ge=0, le=100, description="Independent board members percentage")
    log_legal_costs_paid_for_controversies: Optional[float] = Field(default=None, ge=0, le=100, description="Log legal costs paid for controversies")
    intensity_scope_1: Optional[float] = Field(default=None, ge=0, le=100, description="Intensity scope 1")
    intensity_scope_2: Optional[float] = Field(default=None, ge=0, le=100, description="Intensity scope 2")
    intensity_scope_3: Optional[float] = Field(default=None, ge=0, le=100, description="Intensity scope 3")
    intensity_energy: Optional[float] = Field(default=None, ge=0, le=100, description="Intensity energy")
    intensity_waste: Optional[float] = Field(default=None, ge=0, le=100, description="Intensity waste")
    intensity_water: Optional[float] = Field(default=None, ge=0, le=100, description="Intensity water")
    intensity_training: Optional[float] = Field(default=None, ge=0, le=100, description="Intensity training")
    intensity_productivity: Optional[float] = Field(default=None, ge=0, le=100, description="Intensity productivity")
    revenue_negative_flag: Optional[int] = Field(default=None, ge=0, le=1, description="Revenue negative flag")
    industry_target_enc: Optional[float] = Field(default=None, description="Industry target encoding (auto-computed)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "primary_industry": "Technology",
                "log_market_cap": 20.5,
                "log_employees": 8.1,
                "log_revenue_wins": 15.2,
                "log_scope_1": 4.5,
                "log_scope_2": 3.2,
                "log_scope_3": 5.1,
                "log_energy_consumption": 6.8,
                "log_waste_production": 3.4,
                "log_water_consumption": 7.2,
                "log_hours_of_training_wins": 5.0,
                "log_ceo_compensation": 14.5,
                "independent_board_members_percentage": 65.0,
                "log_legal_costs_paid_for_controversies": 0.0,
                "intensity_scope_1": 0.5,
                "intensity_scope_2": 0.3,
                "intensity_scope_3": 1.2,
                "intensity_energy": 0.8,
                "intensity_waste": 0.1,
                "intensity_water": 0.9,
                "intensity_training": 0.4,
                "intensity_productivity": 1.5,
                "revenue_negative_flag": 0,
            }
        }
    )

    @field_validator('*', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty strings to None."""
        if isinstance(v, str) and v.strip() == '':
            return None
        return v

    @field_validator('primary_industry', mode='before')
    @classmethod
    def normalize_primary_industry(cls, value):
        if value is None:
            return 'Technology'
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or 'Technology'
        return value

    @model_validator(mode='after')
    def ensure_at_least_one_feature(self):
        numeric_fields = [
            self.log_market_cap,
            self.log_employees,
            self.log_revenue_wins,
            self.log_scope_1,
            self.log_scope_2,
            self.log_scope_3,
            self.log_energy_consumption,
            self.log_waste_production,
            self.log_water_consumption,
            self.log_hours_of_training_wins,
            self.log_ceo_compensation,
            self.independent_board_members_percentage,
            self.log_legal_costs_paid_for_controversies,
            self.intensity_scope_1,
            self.intensity_scope_2,
            self.intensity_scope_3,
            self.intensity_energy,
            self.intensity_waste,
            self.intensity_water,
            self.intensity_training,
            self.intensity_productivity,
            self.revenue_negative_flag,
        ]

        if all(value is None for value in numeric_fields):
            raise ValueError('At least one prediction feature must be provided')

        return self


class LoginRequest(BaseModel):
    """Validation schema for login input."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)


class RegisterRequest(BaseModel):
    """Validation schema for registration input."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=255)


class ForgotPasswordRequest(BaseModel):
    """Validation schema for forgot password input."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Validation schema for reset password input."""
    token: str = Field(..., min_length=20, max_length=500)
    new_password: str = Field(..., min_length=8, max_length=255)


class UpdateProfileRequest(BaseModel):
    """Validation schema for profile update input."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    current_password: Optional[str] = Field(default=None, min_length=8, max_length=255)
    new_password: Optional[str] = Field(default=None, min_length=8, max_length=255)

    @field_validator('*', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if isinstance(v, str) and v.strip() == '':
            return None
        return v
