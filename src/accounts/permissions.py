import logging
from rest_framework import permissions


class IsMisUser(permissions.BasePermission):
    def has_permission(self, request, view):
        #logging.info(f'IsMisUser:has_permission: User:{request.user}')
        if not request.user.is_authenticated:
            logging.info(f'IsMisUser:has_permission: User:{request.user}. NotAuthenticated. Return False')
            return False
        if request.user.is_superuser:
            logging.info(f'IsMisUser:has_permission: User:{request.user}. IS_SUPERUSER. Return False')
            return False
        if request.user.is_staff:
            logging.info(f'IsMisUser:has_permission: User:{request.user}. IS_STAFF. Return False')
            return False
        #logging.info(f'IsMisUser:has_permission: User:{request.user}. Authorized. Return True')
        return True

    def has_object_permission(self, request, view, obj):
        logging.info(f'IsMisUser:has_object_permission: obj.user:{obj.mis_user}, \
            request.user:{request.user}, \
            is_staff:{request.user.is_staff}, \
            is_super"{request.user.is_superuser}')
        if request.user.is_superuser == True:
            logging.info(f'IsMisUser:has_object_permission: IS_SUPERUSER. Return False')
            return False

        # if obj.mis_id.mis_type != 'M':
        #     return False

        if obj.mis_user == request.user:
            #logging.info(f'IsMisUser:has_object_permission: Owner. return True')
            return True
        logging.info(f'IsMisUser:has_object_permission: Not Owner. return False')
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        logging.info(f'IsOwnerOrReadOnly:has_object_permission: obj.user:{obj.mis_user} \
            request.user:{request.user}, request.method:{request.method}')
        if request.method in permissions.SAFE_METHODS:
            logging.info(f'IsOwnerOrReadOnly:has_object_permission: SAFE_METHODS. return True')
            return True
        if obj.mis_user == request.user:
            logging.info(f'IsOwnerOrReadOnly:has_object_permission: Owner. return True')
            return True
        else:
            logging.info(f'IsOwnerOrReadOnly:has_object_permission: Not Owner. return False')
            return False


class IsMisOrSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        logging.info(f'IsMisOrSuperuser:has_permission: User:{request.user}')
        if not request.user.is_authenticated:
            logging.info(f'IsMisOrSuperuser:has_permission: NotAuthenticated. Return False')
            return False
        if request.user.is_superuser:
            logging.info(f'IsMisOrSuperuser:has_permission: IS_SUPERUSER. Return True')
            return True
        if request.user.is_staff:
            logging.info(f'IsMisOrSuperuser:has_permission: IS_STAFF. Return False')
            return False
        logging.info(f'IsMisOrSuperuser:has_permission: Authorized. Return True')
        return True

    def has_object_permission(self, request, view, obj):
        logging.info(f'IsMisOrSuperuser:has_object_permission: obj.user:{obj.mis_user}, \
            request.user:{request.user}, \
            is_staff:{request.user.is_staff}, \
            is_super"{request.user.is_superuser}')
        # print("has_object_permission:Owner: ", obj.mis_user)
        # print("has_object_permission:Request: ", request.user)
        # print("has_object_permission:Is superuser: ", request.user.is_superuser)
        # print("has_object_permission:Is staff: ", request.user.is_staff)
        if request.user.is_superuser == True:
            logging.info(f'IsMisOrSuperuser:has_object_permission: IS_SUPERUSER. Return True')
            return True
        if obj.mis_user == request.user:
            logging.info(f'IsMisOrSuperuser:has_object_permission: Owner. return True')
            return True
        else:
            logging.info(f'IsMisOrSuperuser:has_object_permission: Not Owner. return False')
            return False
