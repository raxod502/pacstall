#!/bin/env python3

"""Config command."""

#     ____                  __        ____
#    / __ \____ ___________/ /_____ _/ / /
#   / /_/ / __ `/ ___/ ___/ __/ __ `/ / /
#  / ____/ /_/ / /__(__  ) /_/ /_/ / / /
# /_/    \__,_/\___/____/\__/\__,_/_/_/
#
# Copyright (C) 2020-2021
#
# This file is part of Pacstall
#
# Pacstall is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License
#
# Pacstall is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pacstall. If not, see <https://www.gnu.org/licenses/>.

from logging import getLogger
from os import environ
from subprocess import run

from pacstall.api.config_facade import PACSTALL_CONFIG_PATH, read_config
from pacstall.api.error_codes import ErrorCodes, PacstallError

__FALLBACK_EDITOR = "sensible-editor"


async def open_editor() -> int:
    """
    Opens the `config.toml` file in the default editor, and validates it.

    Prioritization order: `PacstallConfig.settings.preferred_editor` > `$PACSTALL_EDITOR` > `$EDITOR` > `sensible-editor`.

    Returns
    -------
    - Editor's `exit code` if it closes with a non-zero exit code
    - `ErrorCodes` if the config validation fails
    - `0` if success
    """

    log = getLogger()
    editor = __FALLBACK_EDITOR

    # Read config to get the `editor`. Continue even if errors exists.
    try:
        conf = await read_config()
        editor = (
            conf.settings.editor
            if conf.settings.editor is not None
            else environ.get(
                "PACSTALL_EDITOR", environ.get("EDITOR", __FALLBACK_EDITOR)
            )
        )
    except PacstallError as error:
        pass
    except Exception as error:
        log.exception(f"Unknown error has occurred. {error}")

    # Open `config.toml` using the editor
    ret_code = run(["sudo", editor, PACSTALL_CONFIG_PATH]).returncode
    if ret_code != 0:
        log.exception(f"Editor '{editor}' closed with a non-zero exit code {ret_code}")
        return ret_code

    # Read the config again to check for errors after editing
    try:
        conf = await read_config()
    except PacstallError as error:
        return error.code
    except Exception as error:
        log.exception(f"Unknown error has occurred. {error}")
        return ErrorCodes.SOFTWARE_ERROR

    return 0