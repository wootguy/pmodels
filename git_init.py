import os, shutil, subprocess, sys, json
import requests
from github import Github

models_path = 'models/player/'
all_dirs = [dir for dir in os.listdir(models_path) if os.path.isdir(os.path.join(models_path,dir))]
all_dirs.sort()
total_dirs = len(all_dirs)
git_asset_root = '.git_data'
username = 'wootdata'
commit_user = 'wootguy'
commit_email = 'w00tguy123@gmail.com'
ssh_host_name = 'wootdata.github.com' # used to select an ssh key from ~/.ssh/config (this is an alias not a real host name)
num_buckets = 32

access_token = ''
with open('access_token.txt', 'r') as file:
    access_token = file.read().replace('\n', '')

github = Github(access_token)

lowest_count = 99999

def hash_string(str):
	hash = 0

	for i in range(0, len(str)):
		char = ord(str[i])
		hash = ((hash<<5)-hash) + char
		hash = hash % 15485863 # prevent hash ever increasing beyond 31 bits (prime)

	return hash 

def create_repos():
	print("")
	print("WARNING: This will delete all sc_models_* repos, locally and on GitHub.")
	print("The repos will then be recreated which will take a long time.")
	print("")

	input("Press Enter to continue...")

	if os.path.exists(git_asset_root):
		shutil.rmtree(git_asset_root)
	os.mkdir(git_asset_root)

	print("Initializing asset repos")
	for i in range(0, num_buckets):
		git_path = os.path.join(git_asset_root, 'repo%s' % i)
		
		args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'init']
		subprocess.run(args)
		
		# configure commit username/email
		args = ['git', '--git-dir=%s' % git_path, 'config', 'user.name', '"%s"' % commit_user]
		subprocess.run(args)
		args = ['git', '--git-dir=%s' % git_path, 'config', 'user.email', '"%s"' % commit_email]
		subprocess.run(args)

	# Add files to each repo, balanced by hash key
	print("Adding files to repos")
	for idx, dir in enumerate(all_dirs):
		b = hash_string(dir) % num_buckets
		git_path = os.path.join(git_asset_root, 'repo%s' % b)
		
		print("%s -> %s" % (dir, git_path))
		
		args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'add', os.path.join(models_path, dir), '-f']
		subprocess.run(args)

	# add common files and commit in all repos
	for i in range(0, num_buckets):
		git_path = os.path.join(git_asset_root, 'repo%s' % i)
		args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'add', '.nojekyll']
		subprocess.run(args)
		args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'commit', '-m', 'initial commit']
		subprocess.run(args)

	github_user = github.get_user()

	# Create repos, push to them, and enable github pages
	for i in range(0, num_buckets):
		git_path = os.path.join(git_asset_root, 'repo%s' % i)
		repo_name = 'scmodels_data_%s' % i

		try:
			repo = github_user.get_repo(repo_name)
			print("Deleting existing repo: %s" % repo_name)
			if repo:
				repo.delete()
		except Exception as e:
			print(e)
			
		repo = github_user.create_repo(repo_name, description='storage partition for scmodels')
		print("Created %s" % repo.full_name)
		
		args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'remote', 'add', 'origin', 'git@%s:%s.git' % (ssh_host_name, repo.full_name)]
		subprocess.run(args)
		
		args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'push', '-u', 'origin', 'master']
		subprocess.run(args)
		
		print("Enabling GitHub Pages...")
		headers = {
			'Authorization': 'token ' + access_token,
			'Accept': 'application/vnd.github.switcheroo-preview+json'
		}
		payload = {
			'source': {
				'branch': 'master',
				'path': ''
			}
		}
		resp = requests.post('https://api.github.com/repos/%s/%s/pages' % (username, repo_name), headers=headers, data=json.dumps(payload)).json()
		print(resp)
		
		print("Repo creation finished: %s" % repo_name)
		print("")

def update():
	global all_dirs
	
	if True:
		# Add files to each repo, balanced by hash key
		print("Adding files to repos")
		
		with open("updated.txt", "r") as update_list:
			all_dirs = update_list.readlines()
			print("using updated.txt instead of checking all folders")
			
		updated_buckets = []
		
		for idx, dir in enumerate(all_dirs):
			dir = dir.strip()
			b = hash_string(dir) % num_buckets
			updated_buckets.append(b)
			git_path = os.path.join(git_asset_root, 'repo%s' % b)
			
			print("%s -> %s" % (dir, git_path))
			
			args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'add', os.path.join(models_path, dir), '-f']
			subprocess.run(args)
	
	# commit and push
	for i in range(0, num_buckets):
		if i not in updated_buckets:
			continue
			
		repo_name = 'scmodels_data_%s' % i
		print("\nUpdating %s" % repo_name)
		git_path = os.path.join(git_asset_root, 'repo%s' % i)
		args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'commit', '-m', 'add new models']
		subprocess.run(args)
		
		args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'push']
		subprocess.run(args)
		
	os.remove("updated.txt")
	

args = sys.argv[1:]
	
if len(args) == 1 and args[0].lower() == 'help' or len(args) == 0:
	print("\nUsage:")
	print("python3 git_init.py [command]\n")
	
	print("Available commands:")
	print("create - creates or re-creates all data repos (takes like 8 hours)")
	print("update - adds new models")

if len(args) > 0:
	if args[0].lower() == 'create':
		create_repos()
	if args[0].lower() == 'update':
		update()