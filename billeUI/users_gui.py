#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Users module

Module dedicated to create and delete users and for login in and login out.

@author: igna
Created on Sat Sept 03 19:21:22 2022
Refactored on Sun Oct 16 16:00:00 2022
"""
import os
import sys

# from src.misc import info
# from src.users import users_core
# from src.errors import errors

BASE_PATH = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_PATH, "data")

SRCDIR = "/home/igna/Igna/python-scripts/billeterapp/"
sys.path.append(SRCDIR)


def create_user(username: str, useremail: str, password: bytes, password_check: bytes) -> None:
    """
    Creates an user with its directories and entries in the data base.
    Uses inputs for name of the user and password.
    Won't allow you to create an user if it already existis or if you are
    logged in with another users.s
    """
    if not os.getcwd() == DATA_PATH:
        raise errors.WrongDirectoryError
    user_dir = users_core.UsersDirs(username)
    user_db = users_core.UsersDB(username, useremail)
    if os.path.isdir(user_dir.absdirname):
        raise errors.UserAlreadyExistsError(user_db.user)
    if password != password_check:
        raise errors.PasswdsDontMatchError
    user_dir.create_user_dir()
    user_db.add_user_to_db(passwd=password)


def delete_user(username: str, useremail: str, password: bytes, confirmation: bool) -> None:
    """
    Deletes an user and all its information stored in its directories and
    data base.
    Ues inputs for name of the user and password.
    Won't allow you to delete an user if you are logged in with that or
    another user.
    """
    if not os.getcwd() == DATA_PATH:
        raise errors.WrongDirectoryError
    user_dir = users_core.UsersDirs(username)
    user_db = users_core.UsersDB(username, useremail)
    if not os.path.isdir(user_dir.absdirname):
        raise errors.UserDoesNotExistsError(user_db.user)
    user_db.passwd_validation_indb(passwd=password)
    if not user_db.passwdvalidation:
        raise errors.WrongPasswordError
    if not confirmation:
        raise errors.UserCouldNotBeDeletedError(username)
    else:
        user_dir.delete_user_dir()
        user_db.delete_user_indb()


def change_password(
    username: str,
    useremail: str,
    old_password: bytes,
    new_password: bytes,
    check_new_password: bytes,
) -> None:
    """
    Changes the password of a given user.
    Uses inputs for name of the user, old password and new password.
    """
    if not os.getcwd() == DATA_PATH:
        raise errors.WrongDirectoryError
    user_dir = users_core.UsersDirs(username)
    user_db = users_core.UsersDB(username, useremail)
    if not os.path.isdir(user_dir.absdirname):
        raise errors.AccountDoesNotExistError

    user_db.passwd_validation_indb(passwd=old_password)
    if not user_db.passwdvalidation:
        raise errors.WrongPasswordError
    if new_password != check_new_password:
        raise errors.PasswdsDontMatchError
    user_db.change_pass_indb(new_passwd=new_password)


def login(username=None, password=None) -> None:
    """Changes the current working directory to the user's directory"""
    if not os.getcwd() == DATA_PATH:
        raise errors.WrongDirectoryError
    user_dir = users_core.UsersDirs(user=username)
    user_db = users_core.UsersDB(user=username, email="todo@bug.solvethis")
    if not os.path.isdir(user_dir.absdirname):
        raise errors.UserDoesNotExistsError(user_db.user)
    user_db.passwd_validation_indb(password)
    if not user_db.passwdvalidation:
        raise errors.WrongPasswordError
    os.chdir(user_dir.absdirname)
    info.info()


def logout():
    """Changes the current working directory to the base directory"""
    if "USR" in os.getcwd():
        os.chdir(DATA_PATH)
        print("\nSe ha cerrado sesión\n")
    else:
        print("\nNo hay ninguna sesión iniciada.\n")
