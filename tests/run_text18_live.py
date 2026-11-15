#!/usr/bin/env python3
"""TEXT18 adapter to existing auditable runner, without changing old cohort.

Only prompts and allowlisted runtime knowledge reach wrapper. Rubrics stay out.
Generation is not semantic PASS. Existing --check gate targets old cohort, so
it is deliberately rejected here; independent review is required for TEXT18.
"""
import json
import sys
from pathlib import Path
import run_live_model_behavior as runner

def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if '--check' in args:
        raise ValueError('TEXT18 requires independent semantic review; old cohort gate is not applicable')
    runner.CASES=list(json.loads((Path(__file__).parent/'text18_cases.json').read_text()))
    runner.DEFAULT_OUT=Path(__file__).parent.parent/'reports/text18-live'
    return runner.main(args)

if __name__=='__main__':sys.exit(main())
