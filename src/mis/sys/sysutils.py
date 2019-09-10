
def is_mis_admin(user, mis_id):
    # print(f'User: {user.username}, Perms: {user.get_all_permissions()}')
    if user.has_perm("aem_admin"):
        return True
    if not user.has_perm("sys"):
        return False
    mis_s = str(mis_id).zfill(2)
    perm = f'mis{mis_s}'
    if user.has_perm(perm):
        return True
    return False


def is_true_admin(user, mis_id):
    if user.is_superuser:
        return True
    if not user.has_perm("sys"):
        return False
    mis_s = str(mis_id).zfill(2)
    perm = f'mis{mis_s}'
    if user.has_perm(perm):
        return True
    return False


def is_sys(user):
    # print(f'User: {user.username}, Perms: {user.get_all_permissions()}')
    if user.is_superuser:
        return True
    if user.has_perm("aem_admin"):
        return True
    if user.has_perm("sys"):
        return True
    return False
