#include <CoreFoundation/CoreFoundation.h>
#include <Security/Security.h>

#include <stdbool.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    const char *project;
    const char *account;
} project_account;

static const project_account PROJECT_ACCOUNTS[] = {
    {"aisoft-platform", "aisoft-platform-agent"},
    {"hsdb", "hsdb-agent"},
    {"myapp", "myapp-agent"},
    {"newemaint", "newemaint-agent"},
    {"rsdesign-new", "rsdesign-agent"},
    {"sap-table-migrate", "sap-table-migrate-agent"},
    {"sfm-digital-board", "sfm-board-agent"},
    {"smoke-test", "smoke-test-agent"},
    {"wmpda", "wmpda-agent"},
};

static const char *project_agent(const char *project) {
    size_t count = sizeof(PROJECT_ACCOUNTS) / sizeof(PROJECT_ACCOUNTS[0]);
    for (size_t index = 0; index < count; index++) {
        if (strcmp(PROJECT_ACCOUNTS[index].project, project) == 0) {
            return PROJECT_ACCOUNTS[index].account;
        }
    }
    return NULL;
}

static bool exact_item_acl(const char *service, const char *account) {
    CFStringRef service_value = CFStringCreateWithCString(
        kCFAllocatorDefault, service, kCFStringEncodingUTF8
    );
    CFStringRef account_value = CFStringCreateWithCString(
        kCFAllocatorDefault, account, kCFStringEncodingUTF8
    );
    if (service_value == NULL || account_value == NULL) {
        return false;
    }
    const void *keys[] = {
        kSecClass, kSecAttrService, kSecAttrAccount, kSecReturnRef, kSecMatchLimit,
    };
    const void *values[] = {
        kSecClassGenericPassword, service_value, account_value, kCFBooleanTrue,
        kSecMatchLimitAll,
    };
    CFDictionaryRef query = CFDictionaryCreate(
        kCFAllocatorDefault, keys, values, 5,
        &kCFTypeDictionaryKeyCallBacks, &kCFTypeDictionaryValueCallBacks
    );
    CFTypeRef raw_result = NULL;
    OSStatus status = SecItemCopyMatching(query, &raw_result);
    CFRelease(query);
    CFRelease(service_value);
    CFRelease(account_value);
    if (status != errSecSuccess || raw_result == NULL
            || CFGetTypeID(raw_result) != CFArrayGetTypeID()
            || CFArrayGetCount((CFArrayRef)raw_result) != 1) {
        if (raw_result != NULL) CFRelease(raw_result);
        return false;
    }

    SecKeychainItemRef item = (SecKeychainItemRef)CFArrayGetValueAtIndex(
        (CFArrayRef)raw_result, 0
    );
    SecKeychainRef default_keychain = NULL;
    SecKeychainRef item_keychain = NULL;
    SecAccessRef access = NULL;
    bool valid = (
        SecKeychainCopyDefault(&default_keychain) == errSecSuccess
        && SecKeychainItemCopyKeychain(item, &item_keychain) == errSecSuccess
        && default_keychain != NULL && item_keychain != NULL
        && CFEqual(default_keychain, item_keychain)
        && SecKeychainItemCopyAccess(item, &access) == errSecSuccess
        && access != NULL
    );

    CFArrayRef decrypt_acls = NULL;
    CFArrayRef applications = NULL;
    CFStringRef description = NULL;
    SecKeychainPromptSelector prompt_selector = 0;
    SecTrustedApplicationRef expected_application = NULL;
    CFDataRef actual_data = NULL;
    CFDataRef expected_data = NULL;
    if (valid) {
        decrypt_acls = SecAccessCopyMatchingACLList(
            access, kSecACLAuthorizationDecrypt
        );
        valid = decrypt_acls != NULL && CFArrayGetCount(decrypt_acls) == 1;
    }
    if (valid) {
        SecACLRef acl = (SecACLRef)CFArrayGetValueAtIndex(decrypt_acls, 0);
        valid = SecACLCopyContents(
            acl, &applications, &description, &prompt_selector
        ) == errSecSuccess;
        valid = valid && applications != NULL && CFArrayGetCount(applications) == 1;
    }
    if (valid) {
        SecTrustedApplicationRef actual_application =
            (SecTrustedApplicationRef)CFArrayGetValueAtIndex(applications, 0);
        valid = SecTrustedApplicationCreateFromPath(
            "/usr/bin/security", &expected_application
        ) == errSecSuccess;
        valid = valid && SecTrustedApplicationCopyData(
            actual_application, &actual_data
        ) == errSecSuccess;
        valid = valid && SecTrustedApplicationCopyData(
            expected_application, &expected_data
        ) == errSecSuccess;
        valid = valid && actual_data != NULL && expected_data != NULL
            && CFEqual(actual_data, expected_data)
            && (prompt_selector & kSecKeychainPromptRequirePassphase) == 0;
    }

    if (expected_data != NULL) CFRelease(expected_data);
    if (actual_data != NULL) CFRelease(actual_data);
    if (expected_application != NULL) CFRelease(expected_application);
    if (description != NULL) CFRelease(description);
    if (applications != NULL) CFRelease(applications);
    if (decrypt_acls != NULL) CFRelease(decrypt_acls);
    if (access != NULL) CFRelease(access);
    if (item_keychain != NULL) CFRelease(item_keychain);
    if (default_keychain != NULL) CFRelease(default_keychain);
    CFRelease(raw_result);
    return valid;
}

static void print_item(
    const char *route, const char *service, const char *account, bool comma
) {
    printf(
        "%s{\"account\":\"%s\",\"item_class\":\"generic-password\","
        "\"password_required\":false,\"permanence\":\"default-user-keychain\","
        "\"route\":\"%s\",\"service\":\"%s\","
        "\"trusted_applications\":[\"/usr/bin/security\"]}",
        comma ? "," : "", account, route, service
    );
}

int main(int argc, char **argv) {
    if (argc != 3 || strcmp(argv[1], "--project") != 0) {
        fputs("exact Keychain ACL audit failed\n", stderr);
        return 20;
    }
    const char *agent = project_agent(argv[2]);
    if (agent == NULL || strcmp(agent, "ci-bot") == 0
            || !exact_item_acl("aisoft.gitea.manager-audit", "aisoft-platform-manager")
            || !exact_item_acl("aisoft.gitea.manager-mutation", "aisoft-platform-manager")
            || !exact_item_acl("aisoft.gitea.project-agent", agent)) {
        fputs("exact Keychain ACL audit failed\n", stderr);
        return 20;
    }

    fputs("{\"items\":[", stdout);
    print_item(
        "manager_audit", "aisoft.gitea.manager-audit",
        "aisoft-platform-manager", false
    );
    print_item(
        "manager_mutation", "aisoft.gitea.manager-mutation",
        "aisoft-platform-manager", true
    );
    print_item("project_agent", "aisoft.gitea.project-agent", agent, true);
    fputs("],\"status\":\"PASS\"}\n", stdout);
    return 0;
}
