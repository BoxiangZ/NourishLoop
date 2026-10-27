"""Import every mapped table before creating test metadata or running migrations."""

from apps.api.modules.catalog import models as catalog_models  # noqa: F401
from apps.api.modules.community import models as community_models  # noqa: F401
from apps.api.modules.identity import models as identity_models  # noqa: F401
from apps.api.modules.recommendations import models as recommendation_models  # noqa: F401
from apps.api.modules.tracking import models as tracking_models  # noqa: F401
