# Copyright Header Template

Add this header to the top of all new Python source files:

```python
# Copyright (c) 2025 Richard Martin and Crank Platform Contributors
# All Rights Reserved.
# This software is proprietary and confidential.
# See LICENSE file in the project root for full license information.
# SPDX-License-Identifier: PROPRIETARY
```

## Usage

### For Python Files

```python
#!/usr/bin/env python3
# Copyright (c) 2025 Richard Martin and Crank Platform Contributors
# All Rights Reserved.
# This software is proprietary and confidential.
# See LICENSE file in the project root for full license information.
# SPDX-License-Identifier: PROPRIETARY

"""Module docstring here."""

import ...
```

### For Shell Scripts

```bash
#!/bin/bash
# Copyright (c) 2025 Richard Martin and Crank Platform Contributors
# All Rights Reserved.
# This software is proprietary and confidential.
# See LICENSE file in the project root for full license information.
# SPDX-License-Identifier: PROPRIETARY

set -e
...
```

### For Dockerfiles

```dockerfile
# Copyright (c) 2025 Richard Martin and Crank Platform Contributors
# All Rights Reserved.
# This software is proprietary and confidential.
# See LICENSE file in the project root for full license information.
# SPDX-License-Identifier: PROPRIETARY

FROM python:3.11-slim
...
```

### For Markdown Documentation

```markdown
<!--
Copyright (c) 2025 Richard Martin and Crank Platform Contributors
All Rights Reserved.
This software is proprietary and confidential.
See LICENSE file in the project root for full license information.
SPDX-License-Identifier: PROPRIETARY
-->

# Document Title
...
```

## Automated Header Addition

You can use this script to add headers to existing files:

```bash
#!/bin/bash
# add-copyright-headers.sh

HEADER_PY="# Copyright (c) 2025 Richard Martin and Crank Platform Contributors
# All Rights Reserved.
# This software is proprietary and confidential.
# See LICENSE file in the project root for full license information.
# SPDX-License-Identifier: PROPRIETARY
"

# Add to all Python files without headers
find src/ services/ scripts/ tests/ -name "*.py" -type f | while read file; do
    if ! grep -q "Copyright" "$file"; then
        echo "Adding header to $file"
        echo "$HEADER_PY" | cat - "$file" > temp && mv temp "$file"
    fi
done
```

## Notes

- **SPDX-License-Identifier**: Using "PROPRIETARY" since this is not open source
- **Year**: Update to current year for new files
- **Contributors**: Automatically includes all contributors
- **Existing Files**: Add headers gradually, prioritize new code first
- **Third-Party Code**: Do NOT add this header to vendored/third-party code
