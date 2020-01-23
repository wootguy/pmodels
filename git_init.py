import os, shutil, subprocess, sys, json
import requests
from github import Github


print("")
print("WARNING: This will delete all sc_models_* repos, locally and on GitHub.")
print("The repos will then be recreated which will take a long time.")
print("")

input("Press Enter to continue...")


models_path = 'models/player/'
all_dirs = [dir for dir in os.listdir(models_path) if os.path.isdir(os.path.join(models_path,dir))]
all_dirs.sort()
total_dirs = len(all_dirs)
git_asset_root = '.git_data'
username = 'wootguy'

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

num_buckets = 16
buckets = []

if os.path.exists(git_asset_root):
	shutil.rmtree(git_asset_root)
os.mkdir(git_asset_root)

print("Initializing asset repos")
for i in range(0, num_buckets):
	git_path = os.path.join(git_asset_root, 'repo%s' % i)
	
	args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'init']
	subprocess.run(args)

for i in range(0, num_buckets):
	buckets.append([])

count = 0

# Add files to each repo, balanced by hash key
print("Adding files to repos")
max_files = 64
for idx, dir in enumerate(all_dirs):
	b = hash_string(dir) % num_buckets
	git_path = os.path.join(git_asset_root, 'repo%s' % b)
	
	print("%s -> %s" % (dir, git_path))
	
	args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'add', os.path.join(models_path, dir), '-f']
	subprocess.run(args)
	
	buckets[b].append(dir)
	
	max_files -= 1
	if max_files <= 0:
		print("Exiting early...")
		break

# commit in all repos
for i in range(0, num_buckets):
	git_path = os.path.join(git_asset_root, 'repo%s' % i)
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
	
	args = ['git', '--git-dir=%s' % git_path, '--work-tree=.', 'remote', 'add', 'origin', 'git@github.com:%s.git' % repo.full_name]
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
	
print("Bucket sizes:")
for i in range(0, num_buckets):
	print("%s = %s" % (i, len(buckets[i])))