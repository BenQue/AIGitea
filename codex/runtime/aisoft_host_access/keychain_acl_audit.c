#include <stdio.h>

/*
 * Compatibility tombstone for the Issue #70 candidate helper.
 *
 * Exact SecKeychainItemCopyAccess calls are intentionally disabled: macOS
 * authorizes ACL inspection per item, which turns one aggregate broker audit
 * into multiple user prompts. Runtime governance uses the fixed
 * /usr/bin/security credential reader and keeps exact ACL inspection as
 * separately recorded bootstrap evidence.
 */
int main(void) {
    fputs("interactive Keychain ACL audit is disabled\n", stderr);
    return 20;
}
