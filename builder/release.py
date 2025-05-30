import shutil

from . import settings


def checkout_branches(main_branch: str, release_branch: str) -> None:
    settings.repo.git.checkout(main_branch)
    settings.repo.remotes.origin.fetch()
    branch_list = [ref.name for ref in settings.repo.remotes.origin.refs]

    branch = f"origin/{release_branch}"
    if branch in branch_list:
        if release_branch in settings.repo.heads:
            settings.repo.git.checkout(release_branch)
        else:
            settings.repo.git.checkout("-b", release_branch, "--track", branch)
    else:
        settings.repo.git.checkout("-b", release_branch)


def merge_branches(main_branch: str, release_branch: str) -> None:
    try:
        settings.repo.git.merge(f"origin/{main_branch}")
        print(f"✅ Merged {main_branch} into {release_branch}")
    except Exception as e:
        print(f"⚠️ Merge conflict or error: {e}")


def clean_ignored_files() -> None:
    for file_path in settings.ignore:
        path = settings.project_root / file_path
        if path.is_dir():
            shutil.rmtree(path)
            settings.repo.index.remove([file_path], r=True)
            print(f"Deleted directory {file_path}")
        elif path.is_file():
            path.unlink()
            settings.repo.index.remove([file_path])
            print(f"Deleted file {file_path}")


def rename_readme() -> None:
    old_path = settings.project_root / "README.md"
    new_path = settings.project_root / f"README.{settings.prj_name}.md"
    if settings.readme and old_path.exists():
        old_path.rename(new_path)
        settings.repo.index.remove([old_path])
        settings.repo.index.add([new_path])
        print(f"Renamed {old_path} to {new_path}")


def commit_and_push(release_branch: str) -> None:
    settings.repo.index.commit(f"Update branch '{release_branch}'")
    print(f"Updated and committed changes on branch '{release_branch}'")

    settings.repo.remotes.origin.push(refspec=f"{release_branch}:{release_branch}")
    print(f"Pushed changes to origin/{release_branch}")


def main(main: str = "main", release: str = "release") -> None:
    checkout_branches(main, release)
    merge_branches(main, release)
    clean_ignored_files()
    rename_readme()
    commit_and_push(release)


if __name__ == "__main__":
    main()
