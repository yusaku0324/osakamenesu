from pydantic import BaseModel, Field, conint, constr, EmailStr, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from datetime import datetime, date


class AuthRequestLink(BaseModel):
    email: EmailStr


class AuthVerifyRequest(BaseModel):
    token: str


class UserPublic(BaseModel):
    id: UUID
    email: EmailStr
    display_name: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None


class FavoriteItem(BaseModel):
    shop_id: UUID
    created_at: datetime


class FavoriteCreate(BaseModel):
    shop_id: UUID


class ProfileCreate(BaseModel):
    name: str
    area: str
    price_min: int
    price_max: int
    bust_tag: str
    service_type: str = "store"
    height_cm: Optional[int] = None
    age: Optional[int] = None
    body_tags: Optional[List[str]] = None
    photos: Optional[List[str]] = None
    contact_json: Optional[dict] = None
    discounts: Optional[List[Dict[str, Any]]] = None
    ranking_badges: Optional[List[str]] = None
    ranking_weight: Optional[int] = None
    status: str = "draft"


class DiscountIn(BaseModel):
    label: str
    description: Optional[str] = None
    expires_at: Optional[str] = None


class Promotion(BaseModel):
    label: str
    description: Optional[str] = None
    expires_at: Optional[str] = None
    highlight: Optional[str] = None


class ProfileDoc(BaseModel):
    id: str
    name: str
    area: str
    price_min: int
    price_max: int
    bust_tag: str
    service_type: str
    store_name: Optional[str] = None
    height_cm: Optional[int] = None
    age: Optional[int] = None
    body_tags: List[str] = Field(default_factory=list)
    photos: List[str] = Field(default_factory=list)
    discounts: List[Dict[str, Any]] = Field(default_factory=list)
    ranking_badges: List[str] = Field(default_factory=list)
    ranking_weight: Optional[int] = None
    status: str = "published"
    today: bool = False
    tag_score: float = 0.0
    ctr7d: float = 0.0
    updated_at: int = Field(..., description="unix ts")
    promotions: List[Dict[str, Any]] = Field(default_factory=list)
    review_score: Optional[float] = None
    review_count: Optional[int] = None
    review_highlights: List[Dict[str, Any]] = Field(default_factory=list)
    ranking_reason: Optional[str] = None
    staff_preview: Optional[Any] = None
    price_band: Optional[str] = None
    price_band_label: Optional[str] = None
    has_promotions: Optional[bool] = None
    has_discounts: Optional[bool] = None
    promotion_count: Optional[int] = None
    ranking_score: Optional[float] = None
    diary_count: Optional[int] = None
    has_diaries: Optional[bool] = None
    diary_count: Optional[int] = None
    has_diaries: Optional[bool] = None
    diary_count: Optional[int] = None
    has_diaries: Optional[bool] = None


class AvailabilityOut(BaseModel):
    date: str  # YYYY-MM-DD
    is_today: bool = False
    slots_json: Optional[Dict[str, Any]] = None


class ProfileDetail(BaseModel):
    id: str
    name: str
    area: str
    price_min: int
    price_max: int
    bust_tag: str
    service_type: str = "store"
    store_name: Optional[str] = None
    height_cm: Optional[int] = None
    age: Optional[int] = None
    body_tags: List[str] = Field(default_factory=list)
    photos: List[str] = Field(default_factory=list)
    discounts: List[Dict[str, Any]] = Field(default_factory=list)
    ranking_badges: List[str] = Field(default_factory=list)
    ranking_weight: Optional[int] = None
    status: str = "published"
    today: bool = False
    availability_today: Optional[AvailabilityOut] = None
    outlinks: List[Dict[str, str]] = Field(default_factory=list)  # [{kind, token}]


class ProfileMarketingUpdate(BaseModel):
    discounts: Optional[List[DiscountIn]] = None
    ranking_badges: Optional[List[str]] = None
    ranking_weight: Optional[int] = None


class FacetValue(BaseModel):
    value: str
    label: Optional[str] = None
    count: int
    selected: Optional[bool] = None


class ShopSummary(BaseModel):
    id: UUID
    slug: Optional[str] = None
    name: str
    area: str
    area_name: Optional[str] = None
    address: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    service_tags: List[str] = Field(default_factory=list)
    min_price: int = Field(..., ge=0)
    max_price: int = Field(..., ge=0)
    rating: Optional[float] = None
    review_count: Optional[int] = None
    lead_image_url: Optional[str] = None
    badges: List[str] = Field(default_factory=list)
    today_available: Optional[bool] = None
    next_available_at: Optional[datetime] = None
    distance_km: Optional[float] = None
    online_reservation: Optional[bool] = None
    updated_at: Optional[datetime] = None
    ranking_reason: Optional[str] = None
    promotions: List[Promotion] = Field(default_factory=list)
    price_band: Optional[str] = None
    price_band_label: Optional[str] = None
    has_promotions: Optional[bool] = None
    has_discounts: Optional[bool] = None
    promotion_count: Optional[int] = None
    ranking_score: Optional[float] = None


class ShopSearchResponse(BaseModel):
    page: int
    page_size: int
    total: int
    results: List[ShopSummary]
    facets: Dict[str, List[FacetValue]] = Field(default_factory=dict)


class MediaImage(BaseModel):
    url: str
    kind: Optional[str] = None
    caption: Optional[str] = None
    order: Optional[int] = None


class SocialLink(BaseModel):
    platform: str
    url: str
    label: Optional[str] = None


class ContactInfo(BaseModel):
    phone: Optional[str] = None
    line_id: Optional[str] = None
    website_url: Optional[str] = None
    reservation_form_url: Optional[str] = None
    sns: List[SocialLink] = Field(default_factory=list)


class GeoLocation(BaseModel):
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    nearest_station: Optional[str] = None


class MenuItem(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    price: int
    currency: str = "JPY"
    is_reservable_online: bool = True
    tags: List[str] = Field(default_factory=list)


class StaffShift(BaseModel):
    date: date
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    status: Optional[Literal['available', 'limited', 'unavailable']] = None


class StaffSummary(BaseModel):
    id: UUID
    name: str
    alias: Optional[str] = None
    avatar_url: Optional[str] = None
    headline: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    next_shift: Optional[StaffShift] = None
    specialties: List[str] = Field(default_factory=list)
    is_pickup: Optional[bool] = None


class AvailabilitySlot(BaseModel):
    start_at: datetime
    end_at: datetime
    status: Literal['open', 'tentative', 'blocked'] = 'open'
    staff_id: Optional[UUID] = None
    menu_id: Optional[UUID] = None


class AvailabilityDay(BaseModel):
    date: date
    is_today: Optional[bool] = None
    slots: List[AvailabilitySlot]


class AvailabilityCalendar(BaseModel):
    shop_id: UUID
    generated_at: datetime
    days: List[AvailabilityDay]


class HighlightedReview(BaseModel):
    review_id: Optional[UUID] = None
    title: str
    body: str
    score: int
    visited_at: Optional[date] = None
    author_alias: Optional[str] = None


class ReviewItem(BaseModel):
    id: UUID
    profile_id: UUID
    status: Literal['pending', 'published', 'rejected']
    score: int
    title: Optional[str] = None
    body: str
    author_alias: Optional[str] = None
    visited_at: Optional[date] = None
    created_at: datetime
    updated_at: datetime


class ReviewSummary(BaseModel):
    average_score: Optional[float] = None
    review_count: Optional[int] = None
    highlighted: List[HighlightedReview] = Field(default_factory=list)


class ReviewCreateRequest(BaseModel):
    score: conint(ge=1, le=5)
    body: constr(min_length=1, max_length=4000)
    title: Optional[constr(max_length=160)] = None
    author_alias: Optional[constr(max_length=80)] = None
    visited_at: Optional[date] = None


class ReviewListResponse(BaseModel):
    total: int
    items: List[ReviewItem]


class ReviewModerationRequest(BaseModel):
    status: Literal['pending', 'published', 'rejected']


class DiarySnippet(BaseModel):
    id: Optional[UUID] = None
    title: Optional[str] = None
    body: str
    photos: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    published_at: Optional[datetime] = None


class DiaryItem(BaseModel):
    id: UUID
    profile_id: UUID
    title: str
    body: str
    photos: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    created_at: datetime


class DiaryListResponse(BaseModel):
    total: int
    items: List[DiaryItem]


class ShopDetail(ShopSummary):
    description: Optional[str] = None
    catch_copy: Optional[str] = None
    photos: List[MediaImage] = Field(default_factory=list)
    contact: Optional[ContactInfo] = None
    location: Optional[GeoLocation] = None
    menus: List[MenuItem] = Field(default_factory=list)
    staff: List[StaffSummary] = Field(default_factory=list)
    availability_calendar: Optional[AvailabilityCalendar] = None
    reviews: Optional[ReviewSummary] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    diaries: List[DiarySnippet] = Field(default_factory=list)


class ReservationCustomerInput(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    line_id: Optional[str] = None
    remark: Optional[str] = None


class ReservationCustomer(ReservationCustomerInput):
    id: Optional[UUID] = None


class ReservationStatusEvent(BaseModel):
    status: Literal['pending', 'confirmed', 'declined', 'cancelled', 'expired']
    changed_at: datetime
    changed_by: Optional[str] = None
    note: Optional[str] = None


class Reservation(BaseModel):
    id: UUID
    status: Literal['pending', 'confirmed', 'declined', 'cancelled', 'expired']
    shop_id: UUID
    staff_id: Optional[UUID] = None
    menu_id: Optional[UUID] = None
    channel: Optional[str] = None
    desired_start: datetime
    desired_end: datetime
    notes: Optional[str] = None
    customer: ReservationCustomer
    status_history: List[ReservationStatusEvent] = Field(default_factory=list)
    marketing_opt_in: Optional[bool] = None
    created_at: datetime
    updated_at: datetime


class ReservationCreateRequest(BaseModel):
    shop_id: UUID
    staff_id: Optional[UUID] = None
    menu_id: Optional[UUID] = None
    channel: Optional[str] = None
    desired_start: datetime
    desired_end: datetime
    notes: Optional[str] = None
    customer: ReservationCustomerInput
    marketing_opt_in: Optional[bool] = None


class ReservationUpdateRequest(BaseModel):
    status: Optional[Literal['pending', 'confirmed', 'declined', 'cancelled', 'expired']] = None
    staff_id: Optional[UUID] = None
    notes: Optional[str] = None
    response_message: Optional[str] = None
    keep_customer_contacted: Optional[bool] = None


class ReservationAdminSummary(BaseModel):
    id: UUID
    shop_id: UUID
    shop_name: str
    status: Literal['pending', 'confirmed', 'declined', 'cancelled', 'expired']
    desired_start: datetime
    desired_end: datetime
    channel: Optional[str] = None
    notes: Optional[str] = None
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReservationAdminList(BaseModel):
    total: int
    items: list[ReservationAdminSummary]


class ReservationAdminUpdate(BaseModel):
    status: Optional[Literal['pending', 'confirmed', 'declined', 'cancelled', 'expired']] = None
    notes: Optional[str] = None


class AvailabilitySlotIn(BaseModel):
    start_at: datetime
    end_at: datetime
    status: Literal['open', 'tentative', 'blocked'] = 'open'
    staff_id: Optional[UUID] = None
    menu_id: Optional[UUID] = None


class AvailabilityCreate(BaseModel):
    profile_id: UUID
    date: date
    slots: Optional[List[AvailabilitySlotIn]] = None


class AvailabilityUpsert(BaseModel):
    date: date
    slots: Optional[List[AvailabilitySlotIn]] = None


class MenuInput(BaseModel):
    id: Optional[UUID] = None
    name: str
    price: int
    duration_minutes: Optional[int] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_reservable_online: Optional[bool] = True


class StaffInput(BaseModel):
    id: Optional[UUID] = None
    name: str
    alias: Optional[str] = None
    headline: Optional[str] = None
    specialties: List[str] = Field(default_factory=list)


class ShopContactUpdate(BaseModel):
    phone: Optional[str] = None
    line_id: Optional[str] = None
    website_url: Optional[str] = None
    reservation_form_url: Optional[str] = None
    sns: Optional[List[Dict[str, Any]]] = None


class ShopContentUpdate(BaseModel):
    service_tags: Optional[List[str]] = None
    menus: Optional[List[MenuInput]] = None
    staff: Optional[List[StaffInput]] = None
    contact: Optional[ShopContactUpdate] = None
    description: Optional[str] = None
    catch_copy: Optional[str] = None
    address: Optional[str] = None
    photos: Optional[List[str]] = None


class ShopAdminSummary(BaseModel):
    id: UUID
    name: str
    area: str
    status: str
    service_type: str


class ShopAdminList(BaseModel):
    items: List[ShopAdminSummary]


class ShopAdminDetail(BaseModel):
    id: UUID
    name: str
    area: str
    price_min: int
    price_max: int
    service_type: str
    service_tags: List[str] = Field(default_factory=list)
    contact: Dict[str, Any] | None = None
    description: Optional[str] = None
    catch_copy: Optional[str] = None
    address: Optional[str] = None
    photos: List[str] = Field(default_factory=list)
    menus: List[MenuItem] = Field(default_factory=list)
    staff: List[StaffSummary] = Field(default_factory=list)
    availability: List[AvailabilityDay] = Field(default_factory=list)


DASHBOARD_ALLOWED_NOTIFICATION_STATUSES = {
    "pending",
    "confirmed",
    "declined",
    "cancelled",
    "expired",
}

SlackWebhookStr = constr(max_length=200)
LineNotifyTokenStr = constr(min_length=40, max_length=60, pattern=r"^[0-9A-Za-z_-]+$")


class DashboardNotificationChannelEmail(BaseModel):
    enabled: bool = False
    recipients: List[EmailStr] = Field(default_factory=list)

    @field_validator("recipients")
    @classmethod
    def validate_recipients(cls, recipients: List[EmailStr]) -> List[EmailStr]:
        if len(recipients) > 5:
            raise ValueError("メール宛先は最大5件まで設定可能です")
        lowered = [r.lower() for r in recipients]
        if len(lowered) != len(set(lowered)):
            raise ValueError("同じメールアドレスは重複して設定できません")
        return recipients

    @model_validator(mode="after")
    def ensure_enabled_has_recipients(self) -> "DashboardNotificationChannelEmail":
        if self.enabled and not self.recipients:
            raise ValueError("メール通知を有効化するには宛先を設定してください")
        return self


class DashboardNotificationChannelLine(BaseModel):
    enabled: bool = False
    token: Optional[LineNotifyTokenStr] = None

    @field_validator("token", mode="before")
    @classmethod
    def normalize_token(cls, value: Optional[str]) -> Optional[str]:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def ensure_enabled_has_token(self) -> "DashboardNotificationChannelLine":
        if self.enabled and not self.token:
            raise ValueError("LINE 通知を有効化するにはトークンを入力してください")
        return self


class DashboardNotificationChannelSlack(BaseModel):
    enabled: bool = False
    webhook_url: Optional[SlackWebhookStr] = None

    @field_validator("webhook_url")
    @classmethod
    def validate_webhook(cls, url: Optional[str]) -> Optional[str]:
        if url is None:
            return url
        if not url.startswith("https://hooks.slack.com/"):
            raise ValueError("Slack Webhook URL は https://hooks.slack.com/ で始まる必要があります")
        return url

    @model_validator(mode="after")
    def ensure_enabled_has_webhook(self) -> "DashboardNotificationChannelSlack":
        if self.enabled and not self.webhook_url:
            raise ValueError("Slack 通知を有効化するには Webhook URL を入力してください")
        return self


class DashboardNotificationChannels(BaseModel):
    email: DashboardNotificationChannelEmail = Field(default_factory=DashboardNotificationChannelEmail)
    line: DashboardNotificationChannelLine = Field(default_factory=DashboardNotificationChannelLine)
    slack: DashboardNotificationChannelSlack = Field(default_factory=DashboardNotificationChannelSlack)

    def any_enabled(self) -> bool:
        return any((self.email.enabled, self.line.enabled, self.slack.enabled))


class DashboardNotificationSettingsBase(BaseModel):
    channels: DashboardNotificationChannels
    trigger_status: List[Literal['pending', 'confirmed', 'declined', 'cancelled', 'expired']] = Field(default_factory=list)

    @field_validator("trigger_status")
    @classmethod
    def validate_trigger_status(cls, statuses: List[str]) -> List[str]:
        seen: List[str] = []
        for status in statuses:
            if status not in DASHBOARD_ALLOWED_NOTIFICATION_STATUSES:
                raise ValueError(f"未対応のステータスが指定されました: {status}")
            if status not in seen:
                seen.append(status)
        return seen


class DashboardNotificationSettingsInput(DashboardNotificationSettingsBase):
    @model_validator(mode="after")
    def ensure_configuration_valid(self) -> "DashboardNotificationSettingsInput":
        if not self.channels.any_enabled():
            raise ValueError("少なくとも1つの通知チャネルを有効化してください")
        return self


class DashboardNotificationSettingsUpdate(DashboardNotificationSettingsInput):
    updated_at: datetime


class DashboardNotificationSettingsResponse(DashboardNotificationSettingsBase):
    profile_id: UUID
    updated_at: datetime
