from event_driven.core import main
from event_driven.logger import get_logger, propagate_loggers

logger = get_logger(__name__)

propagate_loggers()

if __name__ == "__main__":
    main()
