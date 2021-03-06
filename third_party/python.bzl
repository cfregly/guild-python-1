#-*-python-*-

def guild_python_workspace():

    # We're maintaining our own fork as we have some pending PRs that
    # have not been merged:
    #
    # - https://github.com/pallets/click/pull/860
    #
    native.new_http_archive(
        name = "org_click",
        build_file = "//third_party:click.BUILD",
        urls = [
            "https://github.com/guildai/click/archive/1520fa44dcbe20ebed03f634ddfdffe48c46a799.zip"
        ],
        strip_prefix = "click-1520fa44dcbe20ebed03f634ddfdffe48c46a799",
        sha256 = "cdc599a630613e905770d5d4e87d67a160618541de565d0dc267f11202ca1670",
    )

    # We're building native extensions for our binary releases.
    #
    native.new_http_archive(
        name = "org_psutil",
        build_file = "//third_party:psutil.BUILD",
        urls = [
            "https://pypi.python.org/packages/d3/0a/74dcbb162554909b208e5dbe9f4e7278d78cc27470993e05177005e627d0/psutil-5.3.1.tar.gz"
        ],
        strip_prefix = "psutil-5.3.1",
        sha256 = "12dd9c8abbad15f055e9579130035b38617020ce176f4a498b7870e6321ffa67",
    )
