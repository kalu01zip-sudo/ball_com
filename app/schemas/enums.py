from enum import Enum


class CountryEnum(str, Enum):
    US = "US"
    AU = "AU"
    BR = "BR"
    CA = "CA"
    CN = "CN"
    FR = "FR"
    DE = "DE"
    IN = "IN"
    IT = "IT"
    MX = "MX"
    NL = "NL"
    SG = "SG"
    ES = "ES"
    TR = "TR"
    AE = "AE"
    GB = "GB"
    JP = "JP"
    SA = "SA"
    PL = "PL"
    SE = "SE"
    BE = "BE"
    EG = "EG"
    ZA = "ZA"
    IE = "IE"


class SortByEnum(str, Enum):
    RELEVANCE = "RELEVANCE"
    LOWEST_PRICE = "LOWEST_PRICE"
    HIGHEST_PRICE = "HIGHEST_PRICE"
    REVIEWS = "REVIEWS"
    NEWEST = "NEWEST"
    BEST_SELLERS = "BEST_SELLERS"


class ProductConditionEnum(str, Enum):
    ALL = "ALL"
    NEW = "NEW"
    USED = "USED"
    RENEWED = "RENEWED"
    COLLECTIBLE = "COLLECTIBLE"


class DealsEnum(str, Enum):
    NONE = "NONE"
    ALL_DISCOUNTS = "ALL_DISCOUNTS"
    TODAYS_DEALS = "TODAYS_DEALS"


class ReviewSortEnum(str, Enum):
    TOP_REVIEWS = "TOP_REVIEWS"
    MOST_RECENT = "MOST_RECENT"


class StarRatingEnum(str, Enum):
    ALL = "ALL"
    FIVE_STARS = "5_STARS"
    FOUR_STARS = "4_STARS"
    THREE_STARS = "3_STARS"
    TWO_STARS = "2_STARS"
    ONE_STARS = "1_STARS"
    POSITIVE = "POSITIVE"
    CRITICAL = "CRITICAL"


class BestSellerTypeEnum(str, Enum):
    BEST_SELLERS = "BEST_SELLERS"
    GIFT_IDEAS = "GIFT_IDEAS"
    MOST_WISHED_FOR = "MOST_WISHED_FOR"
    MOVERS_AND_SHAKERS = "MOVERS_AND_SHAKERS"
    NEW_RELEASES = "NEW_RELEASES"


class DealStarRatingEnum(str, Enum):
    ALL = "ALL"
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"


class DealPriceRangeEnum(str, Enum):
    ALL = "ALL"
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"


class DealDiscountRangeEnum(str, Enum):
    ALL = "ALL"
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"


class DealProductSortByEnum(str, Enum):
    FEATURED = "FEATURED"
    LOWEST_PRICE = "LOWEST_PRICE"
    HIGHEST_PRICE = "HIGHEST_PRICE"
    REVIEWS = "REVIEWS"
    NEWEST = "NEWEST"
    BEST_SELLERS = "BEST_SELLERS"


class InfluencerPostScopeEnum(str, Enum):
    ALL = "ALL"
    IDEA_LISTS = "IDEA_LISTS"
    PHOTOS = "PHOTOS"
    VIDEOS = "VIDEOS"