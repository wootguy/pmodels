# sudo apt install libglew-dev libosmesa-dev pngcrush

import sys, os, shutil, collections, json, subprocess, stat, hashlib, traceback, time
from datetime import datetime
from glob import glob
from io import StringIO

# TODO:
# - some models I added _v2 to are actually a completely different model
# - delete all thumbs.db and .ztmp
# - add to alias when renaming

game_id = ''
if os.path.exists('gameid.txt'):
	with open('gameid.txt', 'r') as file:
		game_id = file.read().replace('\n', '')

if not game_id:
	print("Game ID is blank. Create a gameid.txt file and write your game ID there (e.g. hl or sc)")
	sys.exit();

database_dir = 'database/' + game_id + '/'

master_json = {}
master_json_name = database_dir + '/models.json'
hash_json_name = database_dir + '/hashes.json'
replacements_json_name = database_dir + '/replacements.json'
alias_json_name = database_dir + '/alias.json'
versions_json_name = database_dir + '/versions.json'
tags_json_name = database_dir + '/tags.json'
groups_json_name = database_dir + '/groups.json'

start_dir = os.getcwd()

models_path = 'models/player/'
install_path = 'install/'
modelguy_path = os.path.join(start_dir, 'modelguy')
pngcrush_path = 'pngcrush'
magick_path = 'convert'
debug_render = False

FL_CRASH_MODEL = 1   # model that crashes the game or model viewer

# assumes chdir'd to the model directory beforehand
def fix_case_sensitivity_problems(model_dir, expected_model_path, expected_bmp_path, work_path):
	global start_dir
	global models_path

	all_files = [file for file in os.listdir('.') if os.path.isfile(file)]
	icase_model = ''
	icase_preview = ''
	for file in all_files:
		if (file.lower() == expected_model_path.lower()):
			icase_model = file
		if (file.lower() == expected_bmp_path.lower()):
			icase_preview = file

	icase_model_original = icase_model
	icase_preview_original = icase_preview
	icase_model = os.path.splitext(icase_model)[0]
	icase_preview = os.path.splitext(icase_preview)[0]
	
	if (icase_model and icase_model != model_dir) or \
		(icase_preview and icase_preview != model_dir) or \
		(icase_model and icase_preview and icase_model != icase_preview):
		print("\nFound case-sensitive differences:\n")
		print("DIR (1): " + model_dir)
		print("MDL (2): " + icase_model)
		print("BMP (3): " + icase_preview)
		while True:
			x = input("\nWhich capitalization should be used? (enter 1, 2, or 3) ")
			
			correct_name = model_dir
			if x == '1':
				correct_name = model_dir
			elif x == '2':
				correct_name = icase_model
			elif x == '3':
				correct_name = icase_preview
			else:
				continue
			
			rename_model(model_dir, correct_name, work_path)
			
			return correct_name
	return model_dir

def get_sorted_dirs(path):
	all_dirs = [dir for dir in os.listdir(path) if os.path.isdir(os.path.join(path,dir))]
	return sorted(all_dirs, key=str.casefold)

def get_model_modified_date(mdl_name, work_path):
	mdl_path = os.path.join(work_path, mdl_name, mdl_name + ".mdl")
	return int(os.path.getmtime(mdl_path))

def rename_model(old_dir_name, new_name, work_path):
	global master_json
	global master_json_name
	global start_dir
	
	os.chdir(start_dir)
	
	old_dir = os.path.join(work_path, old_dir_name)
	new_dir = os.path.join(work_path, new_name)
	if not os.path.isdir(old_dir):
		print("Can't rename '%s' because that dir doesn't exist" % old_dir)
		return False
	
	if (old_dir_name != new_name and os.path.exists(new_dir)):
		print("Can't rename folder to %s. That already exists." % new_dir)
		return False
	
	if old_dir != new_dir:
		os.rename(old_dir, new_dir)
		print("Renamed %s -> %s" % (old_dir, new_dir))
	os.chdir(new_dir)
	
	all_files = [file for file in os.listdir('.') if os.path.isfile(file)]
	mdl_files = []
	tmdl_files = []
	bmp_files = []
	png_files = []
	json_files = []
	txt_files = []
	for file in all_files:
		if ".mdl" in file.lower():
			mdl_files.append(file)
		#if ".mdl" in file.lower() and (file == old_dir_name + "t.mdl" or file == old_dir_name + "T.mdl"):
		#	tmdl_files.append(file)
		if ".bmp" in file.lower():
			bmp_files.append(file)
		if '_large.png' in file.lower() or '_small.png' in file.lower() or '_tiny.png' in file.lower():
			png_files.append(file)
		if ".json" in file.lower():
			json_files.append(file)
		if ".txt" in file.lower():
			txt_files.append(file)

	if len(mdl_files) > 1:
		print("Multiple mdl files to rename. Don't know what to do")
		sys.exit()
		return False
	if len(tmdl_files) > 1:
		print("Multiple T mdl files to rename. Don't know what to do")
		sys.exit()
		return False
	if len(bmp_files) > 1:
		print("Multiple bmp files to rename. Don't know what to do")
		sys.exit()
		return False
	if len(txt_files) > 1:
		print("Multiple txt files to rename. Don't know what to do")
		sys.exit()
		return False
	if len(json_files) > 1:
		print("Multiple json files to rename. Don't know what to do")
		sys.exit()
		return False
	if len(png_files) > 3:
		print("Too many PNG files found. Don't know what to do")
		sys.exit()
		return False
		
	def rename_file(file_list, new_name, ext):
		if len(file_list) > 0:
			old_file_name = file_list[0]
			new_file_name = new_name + ext
			
			if old_file_name != new_file_name:
				os.rename(old_file_name, new_file_name)
				print("Renamed %s -> %s" % (old_file_name, new_file_name))
			
	rename_file(bmp_files, new_name, '.bmp')
	rename_file(mdl_files, new_name, '.mdl')
	rename_file(tmdl_files, new_name, 't.mdl')
	rename_file(json_files, new_name, '.json')
	rename_file(txt_files, new_name, '.txt')
	
	for png_file in png_files:
		old_file_name = png_file
		
		new_file_name = ''
		if '_large' in old_file_name:
			new_file_name = new_name + "_large.png"
		elif '_small' in old_file_name:
			new_file_name = new_name + "_small.png"
		elif '_tiny' in old_file_name:
			new_file_name = new_name + "_tiny.png"
		
		if old_file_name != new_file_name:
			os.rename(old_file_name, new_file_name)
			print("Renamed %s -> %s" % (old_file_name, new_file_name))

	return True

def handle_renamed_model(model_dir, work_path):
	all_files = [file for file in os.listdir('.') if os.path.isfile(file)]
	model_files = []
	for file in all_files:
		if '.mdl' in file.lower():
			model_files.append(file)
	while len(model_files) >= 1:
		print("\nThe model file(s) in this folder do not match the folder name:\n")
		print("0) " + model_dir)
		for idx, file in enumerate(model_files):
			print("%s) %s" % (idx+1, file))
		print("r) Enter a new name")
		print("d) Delete this model")
		x = input("\nWhich model should be used? ")

		if x == 'd':
			os.chdir(start_dir)
			shutil.rmtree(os.path.join(work_path, model_dir))
			return ''
		elif x == '0':
			if (not rename_model(model_dir, model_dir, work_path)):
				continue
			return model_dir
		elif x == 'r':
			x = input("What should the model name be? ")
			if (not rename_model(model_dir, x, work_path)):
				continue
			return x
		elif x.isnumeric():
			x = int(x) - 1
			if x < 0 or x >= len(model_files):
				continue
			correct_name = os.path.splitext(model_files[idx-1])[0]
			if (not rename_model(model_dir, correct_name, work_path)):
				continue
			return correct_name
		else:
			continue
		return model_dir
	else:
		while True:
			x = input("\nNo models exist in this folder! Delete it? (y/n) ")
			if x == 'y':
				os.chdir(start_dir)
				shutil.rmtree(os.path.join(work_path, model_dir))
				break
			if x == 'n':
				break
	return model_dir
		
def get_lowest_polycount():
	global models_path
	global start_dir
	
	all_dirs = get_sorted_dirs(models_path)
	total_dirs = len(all_dirs)
	
	lowest_count = 99999
	
	for idx, dir in enumerate(all_dirs):
		model_name = dir
		json_path = model_name + ".json"
	
		os.chdir(start_dir)
		os.chdir(os.path.join(models_path, dir))
	
		if os.path.exists(json_path):
			with open(json_path) as f:
				json_dat = f.read()
				dat = json.loads(json_dat, object_pairs_hook=collections.OrderedDict)
				tri_count = int(dat['tri_count'])
				if tri_count < 300 and tri_count >= 0:
					#print("%s = %s" % (model_name, tri_count))
					print(model_name)
	
def check_for_broken_models():
	global models_path
	global start_dir
	
	all_dirs = get_sorted_dirs(models_path)
	total_dirs = len(all_dirs)
	
	for idx, dir in enumerate(all_dirs):
		model_name = dir
		mdl_path = model_name + ".mdl"
	
		os.chdir(start_dir)
		os.chdir(os.path.join(models_path, dir))
	
		if os.path.isfile(mdl_path):
			mdlguy_command = ['modelguy.exe', 'type', mdl_path]
			return_code = subprocess.run(mdlguy_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode
			if return_code == 0:
				print("Bad model: %s" % model_name)
		else:
			print("Missing model: %s" % model_name)

def generate_info_json(model_name, mdl_path, output_path):
	data = {}
	output = ''
	
	if os.path.exists(output_path):
		os.remove(output_path)
	
	try:
		args = [modelguy_path, 'info', mdl_path, output_path]
		output = subprocess.check_output(args)
	except Exception as e:
		output = e
		print(e)

def update_models(work_path, skip_existing=True, skip_on_error=False, errors_only=True, info_only=False, update_master_json=False):
	global master_json
	global master_json_name
	global hash_json_name
	global magick_path
	global pngcrush_path
	global modelguy_path
	global start_dir
	global models_path
	
	os.makedirs(models_path, exist_ok=True)
	
	all_dirs = get_sorted_dirs(work_path)
	total_dirs = len(all_dirs)
	
	list_file = None
	if update_master_json:
		list_file = open(database_dir + "/model_names.txt","w") 
	failed_models = []
	longname_models = []
	
	hash_json = {}
	
	for idx, dir in enumerate(all_dirs):
		model_name = dir
		print("IDX: %s / %s: %s                  " % (idx, total_dirs-1, model_name), end='\r')
		
		#garg.mdl build/asdf 1000x1600 0 1 1
		
		if len(dir) > 22:
			longname_models.append(dir)
		
		os.chdir(start_dir)
		os.chdir(os.path.join(work_path, dir))
		
		mdl_path = model_name + ".mdl"
		bmp_path = model_name + ".bmp"
		
		if not os.path.isfile(mdl_path) or not os.path.isfile(bmp_path):
			if not skip_on_error:
				model_name = dir = fix_case_sensitivity_problems(dir, mdl_path, bmp_path, work_path)
				mdl_path = model_name + ".mdl"
				bmp_path = model_name + ".bmp"
		
		if not os.path.isfile(mdl_path):
			model_name = dir = handle_renamed_model(dir, work_path)
			mdl_path = model_name + ".mdl"
			bmp_path = model_name + ".bmp"
			if not os.path.isfile(mdl_path):
				continue
		
		if errors_only:
			continue
		
		mdl_path = model_name + ".mdl"
		bmp_path = model_name + ".bmp"
		render_path = model_name + "000.png"
		
		info_json_path = model_name + ".json"
		tiny_thumb = model_name + "_tiny.png"
		small_thumb = model_name + "_small.png"
		large_thumb = model_name + "_large.png"
		
		thumbnails_generated = os.path.isfile(tiny_thumb) and os.path.isfile(small_thumb) and os.path.isfile(large_thumb)
		
		anything_updated = False
		broken_model = False
		
		try:
			if (not os.path.isfile(info_json_path) or not skip_existing):
				print("\nGenerating info json...")
				anything_updated = True
				generate_info_json(model_name, mdl_path, info_json_path)
			else:
				pass #print("Info json already generated")
			
			if ((not thumbnails_generated or not skip_existing) and not info_only):
				print("\nRendering hi-rez image...")
				anything_updated = True
				
				with open(os.devnull, 'w') as devnull:
					args = [modelguy_path, 'image', mdl_path, "1000x1600", render_path]
					null_stdout=None if debug_render else devnull
					subprocess.check_call(args, stdout=null_stdout)

					def create_thumbnail(name, size, posterize_colors):
						print("Creating %s thumbnail..." % name)
						final_path = "./%s_%s.png" % (model_name, name)
						subprocess.check_call([magick_path, "./" + render_path, "-resize", size, "-posterize", posterize_colors, '-type', 'truecolormatte', final_path], stdout=null_stdout)
						subprocess.check_call([pngcrush_path, "-ow", "-s", final_path], stdout=null_stdout)

					create_thumbnail("large", "500x800", "255")
					create_thumbnail("small", "125x200", "16")
					create_thumbnail("tiny", "20x32", "8")
					
					os.remove(render_path)
			else:
				pass #print("Thumbnails already generated")
		except Exception as e:
			print(e)
			traceback.print_exc()
			failed_models.append(model_name)
			broken_model = True
			anything_updated = False
			if not skip_on_error:
				sys.exit()
				
		if update_master_json:
			list_file.write("%s\n" % model_name)
		
		if update_master_json:
			filter_dat = {}
			
			if os.path.isfile(info_json_path):
				with open(info_json_path) as f:
					json_dat = f.read()
					infoJson = json.loads(json_dat, object_pairs_hook=collections.OrderedDict)
					
					totalPolys = 0
					totalPolysLd = 0
					hasLdModel = False
					for body in infoJson["bodies"]:
						models = body["models"]
						polys = int(models[0]["polys"])
						
						if len(models) > 1:
							hasLdModel = True
							totalPolysLd += polys
							polys = int(models[len(models)-1]["polys"])
							totalPolys += polys
						else:
							totalPolys += polys
					
					filter_dat['polys'] = totalPolys
					#filter_dat['polys_ld'] = totalPolysLd
					filter_dat['size'] = infoJson["size"]
					filter_dat['date'] = infoJson["date"]
					
					flags = 0
					if broken_model:
						flags |= FL_CRASH_MODEL
					filter_dat['flags'] = flags
					
					hash = infoJson['md5']
					if hash not in hash_json:
						hash_json[hash] = [model_name]
					else:
						hash_json[hash].append(model_name)
					
			master_json[model_name] = filter_dat
			
		os.chdir(start_dir)
			
	if update_master_json:
		with open(master_json_name, 'w') as outfile:
			json.dump(master_json, outfile)
		with open(hash_json_name, 'w') as outfile:
			json.dump(hash_json, outfile)
		list_file.close()
	
	print("\nFinished!")
	
	if len(failed_models):
		print("\nFailed to update these models:")
		for fail in failed_models:
			print(fail)
			
	if len(longname_models):
		print("\nThe following models have names longer than 22 characters and should be renamed:")
		for fail in longname_models:
			print(fail)

def write_updated_models_list():
	global models_path
	global master_json_name
	
	oldJson = {}
	if os.path.exists(master_json_name):
		with open(master_json_name) as f:
			json_dat = f.read()
			oldJson = json.loads(json_dat, object_pairs_hook=collections.OrderedDict)
	
	all_dirs = get_sorted_dirs(models_path)
	
	list_file = open("updated.txt","w") 
	
	for idx, dir in enumerate(all_dirs):				
		if dir not in oldJson:
			list_file.write("%s\n" % dir)
		
	list_file.close()

def validate_model_isolated():

	boxId = 1 # TODO: unique id per request
	fileSizeQuota = '--fsize=8192' # max written/modified file size in KB
	processMax = '--processes=1'
	maxTime = '--time=60'
	modelName = 'white.mdl'

	print("Cleaning up")
	try:
		args = ['isolate', '--box-id=%d' % boxId, '--cleanup']
		output = subprocess.check_output(args)
	except Exception as e:
		print(e)
		print(output)

	print("Initializing isolate")
	output = ''
	try:
		args = ['isolate', '--box-id=%d' % boxId, '--init']
		print(' '.join(args))
		output = subprocess.check_output(args)
	except Exception as e:
		print(e)
		print(output)
		return False
	
	output = output.decode('utf-8').replace("\n", '')
	
	boxPath = os.path.join(output, "box")
	print("Isolate path: %s" % boxPath)
	
	print("Copying files")
	shutil.copyfile(modelName, os.path.join(boxPath, modelName))
	shutil.copyfile('hlms', os.path.join(boxPath, 'hlms'))
	os.chmod(os.path.join(boxPath, 'hlms'), stat.S_IRWXU)
	
	success = False
	
	print("Running hlms")
	output = ''
	try:
		
		args = ['isolate', fileSizeQuota, processMax, maxTime, '--box-id=%d' % boxId, '--run', '--', './hlms', modelName, 'asdf', '16x16', '0', '1', '1']
		print(' '.join(args))
		output = subprocess.check_output(args)
	except Exception as e:
		print(e)
		print(output)
		success = False
	
	print("Cleaning up")
	try:
		args = ['isolate', '--box-id=%d' % boxId, '--cleanup']
		output = subprocess.check_output(args)
	except Exception as e:
		print(e)
		print(output)
	
	return success

def create_list_file():
	global models_path
	global start_dir
	
	all_dirs = get_sorted_dirs(models_path)
	total_dirs = len(all_dirs)
	
	lower_dirs = [dir.lower() for dir in all_dirs]
	
	list_file = open("models.txt","w")
	min_replace_polys = 143 # set this to the default LD poly count ("player-10up")
	
	for idx, dir in enumerate(all_dirs):
		model_name = dir
		json_path = model_name + ".json"
	
		os.chdir(start_dir)
		os.chdir(os.path.join(models_path, dir))
		
		if (idx % 100 == 0):
			print("Progress: %d / %d" % (idx, len(all_dirs)))
	
		if os.path.exists(json_path):
			with open(json_path) as f:
				json_dat = f.read()
				dat = json.loads(json_dat, object_pairs_hook=collections.OrderedDict)
				tri_count = int(dat['tri_count'])
				replace_model = '' # blank = use default LD model
				if '2d_' + model_name.lower() in lower_dirs:
					replace_model = '2d_' + model_name
				if tri_count < min_replace_polys:
					replace_model = model_name
				
				list_file.write("%s / %d / %s / %s\n"  % (model_name.lower(), tri_count, '', replace_model.lower()))
					
	list_file.close()

def hash_md5(model_file, t_model_file):
	hash_md5 = hashlib.md5()
	with open(model_file, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)
	if t_model_file:
		with open(t_model_file, "rb") as f:
			for chunk in iter(lambda: f.read(4096), b""):
				hash_md5.update(chunk)
	return hash_md5.hexdigest()

def load_all_model_hashes(path):
	global start_dir
	
	print("Loading model hashes in path: %s" % path)
	
	all_dirs = get_sorted_dirs(path)
	total_dirs = len(all_dirs)
	
	model_hashes = {}

	for idx, dir in enumerate(all_dirs):
		model_name = dir
		json_path = model_name + ".json"
	
		os.chdir(start_dir)
		os.chdir(os.path.join(path, dir))
		
		if (idx % 100 == 0):
			print("Progress: %d / %d" % (idx, len(all_dirs)), end="\r")
	
		if os.path.exists(json_path):
			with open(json_path) as f:
				json_dat = f.read()
				dat = json.loads(json_dat, object_pairs_hook=collections.OrderedDict)		
				if 'md5' not in dat:
					os.remove(json_path)
					print("\nMissing hash for %s. Deleted the json for it." % json_path)
					continue
				hash = dat['md5']
				
				if hash not in model_hashes:
					model_hashes[hash] = [model_name]
				else:
					model_hashes[hash].append(model_name)
		else:
			print("\nMissing info JSON for %s" % model_name)
			
	print("Progress: %d / %d" % (len(all_dirs), len(all_dirs)))
	os.chdir(start_dir)
	
	return model_hashes

# it takes a long time to load model hashes for thousands of models, so the list of hashes is saved
# in a single file whenever the database is updated. This loads much faster.
def load_cached_model_hashes():
	global hash_json_name
	
	with open(hash_json_name) as f:
		json_dat = f.read()
		return json.loads(json_dat, object_pairs_hook=collections.OrderedDict)
		
	return None
		

def find_duplicate_models(work_path):	
	model_hashes = load_all_model_hashes(work_path)
	print("\nAll duplicates:")
	
	for hash in model_hashes:
		if len(model_hashes[hash]) > 1:
			print("%s" % model_hashes[hash])
	
	to_delete = []
	
	for hash in model_hashes:
		if len(model_hashes[hash]) > 1:
			print("")
			for idx, model in enumerate(model_hashes[hash]):
				print("%d) %s" % (idx, model))
			keepIdx = int(input("Which model to keep (pick a number)?"))

			for idx, model in enumerate(model_hashes[hash]):
				if idx == keepIdx:
					continue
				to_delete.append(model)
	
	'''
	print("\nDuplicates with %s prefix:" % prefix)
	prefix = "bio_"
	for hash in model_hashes:
		if len(model_hashes[hash]) > 1:
			total_rem = 0
			for model in model_hashes[hash]:
				if model.lower().startswith(prefix):
					to_delete.append(model)
					total_rem += 1
					
			if total_rem == len(model_hashes[hash]):
				print("WOW HOW THAT HAPPEN %s" % model_hashes[hash])
				input("Press enter if this is ok")
	'''
	
	'''
	print("\nDuplicates with the same names:")
	for hash in model_hashes:
		if len(model_hashes[hash]) > 1:
			same_names = True
			first_name = model_hashes[hash][0].lower()
			for name in model_hashes[hash]:
				if name.lower() != first_name:
					same_names = False
					break
			if not same_names:
				continue

			print("%s" % model_hashes[hash])
			to_delete += model_hashes[hash][1:]
	'''
	
	all_dirs = get_sorted_dirs(work_path)
	all_dirs_lower = [dir.lower() for dir in all_dirs]
	unique_dirs_lower = sorted(list(set(all_dirs_lower)))
	
	for ldir in unique_dirs_lower:
		matches = []
		for idx, dir2 in enumerate(all_dirs_lower):
			if dir2 == ldir:
				matches.append(all_dirs[idx])
		if len(matches) > 1:
			msg = ', '.join(["%s (%s)" % (dir, get_model_modified_date(dir, work_path)) for dir in matches])
			print("Conflicting model names: %s" % msg)
	
	if (len(to_delete) == 0):
		print("\nNo duplicates to remove")
		return False
	
	print("\nMarked for deletion:")
	for dir in to_delete:
		print(dir)
	
	input("Press enter to delete the above %s models" % len(to_delete))
	
	os.chdir(start_dir)
	for dir in to_delete:
		shutil.rmtree(os.path.join(work_path, dir))
		
	return True

def get_latest_version_name(model_name, versions_json):
	for vergroup in versions_json:
		for veridx in range(0, len(vergroup)):
			if vergroup[veridx] == model_name:
				return vergroup[0]
				
	return model_name

def fix_json():
	global versions_json_name
	global tags_json_name
	global groups_json_name
	global replacements_json_name
	
	versions_json = None
	tags_json = None
	groups_json = None
	replacements_json = None
	
	with open(versions_json_name) as f:
		versions_json = json.loads(f.read(), object_pairs_hook=collections.OrderedDict)
	with open(tags_json_name) as f:
		tags_json = json.loads(f.read(), object_pairs_hook=collections.OrderedDict)
	with open(groups_json_name) as f:
		groups_json = json.loads(f.read(), object_pairs_hook=collections.OrderedDict)
	
	num_updates = 0
	
	if os.path.exists(replacements_json_name):
		print("-- Checking replacements")
		new_replacement_json = {}
		with open(replacements_json_name) as f:
			replacements_json = json.loads(f.read(), object_pairs_hook=collections.OrderedDict)
		for key, replacements in replacements_json.items():
			print("%s                    " % (key), end='\r')
			
			for idx in range(0, len(replacements)):
				latest_name = get_latest_version_name(replacements[idx], versions_json)
				if latest_name != replacements[idx]:
					print("%s -> %s                    " % (replacements[idx], latest_name))
					replacements[idx] = latest_name
					num_updates += 1
			
			latest_name = get_latest_version_name(key, versions_json)
			if latest_name != key:
				new_replacement_json[latest_name] = replacements
				print("%s -> %s                    " % (key, latest_name))
				num_updates += 1
			else:
				new_replacement_json[key] = replacements
		replacements_json = new_replacement_json
	
	print("-- Checking tags")
	for key, group in tags_json.items():
		print("%s                    " % (key), end='\r')
		
		for idx in range(0, len(group)):
			latest_name = get_latest_version_name(group[idx], versions_json)
			
			if latest_name != group[idx]:
				print("%s -> %s                    " % (group[idx], latest_name))
				group[idx] = latest_name
				num_updates += 1
				
		tags_json[key] = sorted(tags_json[key])
		
	print("\n-- Checking groups")
	for key, group in groups_json.items():
		print("%s                    " % (key), end='\r')
		
		for idx in range(0, len(group)):
			latest_name = get_latest_version_name(group[idx], versions_json)
			
			if latest_name != group[idx]:
				print("%s -> %s                    " % (group[idx], latest_name))
				group[idx] = latest_name
				num_updates += 1
			
		# don't sort so that most appropraite model can be placed as group thumbnail
		#groups_json[key] = sorted(groups_json[key])
	
	with open(tags_json_name, 'w') as outfile:
		tags_json = dict(sorted(tags_json.items()))
		json.dump(tags_json, outfile, indent=4)
	print("Wrote %s " % tags_json_name)
		
	with open(groups_json_name, 'w') as outfile:
		groups_json = dict(sorted(groups_json.items()))
		json.dump(groups_json, outfile, indent=4)
	print("Wrote %s " % groups_json_name)
	
	with open(replacements_json_name, 'w') as outfile:
		groups_json = dict(sorted(groups_json.items()))
		json.dump(replacements_json, outfile, indent=4)
	print("Wrote %s " % replacements_json_name)
	
	print("\nUpdated %d model references to the latest version" % num_updates)

def install_new_models(new_versions_mode=False):
	global models_path
	global install_path
	global alias_json_name
	global versions_json_name
	global start_dir

	
	new_dirs = get_sorted_dirs(install_path)
	if len(new_dirs) == 0:
		print("No models found in %s" % install_path)
		sys.exit()
	
	alt_names = {}
	if os.path.exists(alias_json_name):
		with open(alias_json_name) as f:
			json_dat = f.read()
			alt_names = json.loads(json_dat, object_pairs_hook=collections.OrderedDict)
	
	blacklisted = []
	blacklist_path = database_dir + "/blacklist.txt"
	if os.path.exists(blacklist_path):
		with open(blacklist_path, "r") as f:
			blacklisted = f.read().splitlines()
	
	# First generate info jsons, if needed
	print("-- Generating info JSONs for new models")
	update_models(install_path, True, True, False, True, False)
	
	print("\n-- Checking for duplicates")
	
	any_dups = False
	install_hashes = load_all_model_hashes(install_path)
	
	for hash in install_hashes:
		if len(install_hashes[hash]) > 1:
			msg = ''
			for model in install_hashes[hash]:
				msg += ' ' + model
			print("ERROR: Duplicate models in install folder:" + msg)
			any_dups = True
	
	model_hashes = load_cached_model_hashes()
	dups = []
	
	for hash in install_hashes:
		if hash in model_hashes:
			print("ERROR: %s is a duplicate of %s" % (install_hashes[hash], model_hashes[hash]))
			dups += install_hashes[hash]
			any_dups = True
			
			primary_name = model_hashes[hash][0].lower()
			for alt in install_hashes[hash]:
				alt = alt.lower()
				if alt == primary_name:
					continue
				if primary_name not in alt_names:
					alt_names[primary_name] = []
				if alt not in alt_names[primary_name]:
					alt_names[primary_name].append(alt)
		if hash in blacklisted:
			print("ERROR: %s is a blacklisted model" % install_hashes[hash])
			any_dups = True
	
	with open(alias_json_name, 'w') as outfile:
		json.dump(alt_names, outfile, indent=4)
	
	if len(dups) > 0 and input("\nDelete the duplicate models in the install folder? (y/n)") == 'y':
		for dup in dups:
			path = os.path.join(install_path, dup)
			shutil.rmtree(path)
		new_dirs = get_sorted_dirs(install_path)
	
	old_dirs = [dir for dir in os.listdir(models_path) if os.path.isdir(os.path.join(models_path,dir))]
	old_dirs_lower = [dir.lower() for dir in old_dirs]
	
	alt_name_risk = False
	
	for dir in new_dirs:
		lowernew = dir.lower()
		is_unique_name = True
		
		for idx, old in enumerate(old_dirs):
			if lowernew == old.lower():
				if new_versions_mode:
					is_unique_name = False
				else:
					print("ERROR: %s already exists" % old)
					any_dups = True
					#rename_model(old, old + "_v2", models_path)
		
		if is_unique_name and new_versions_mode:
			any_dups = True
			print("ERROR: %s is not an update to any model. No model with that name exists." % dir)
		
		if not new_versions_mode:
			# not checking alias in new version mode because the models will be renamed
			# altough technically there can be an alias problem still, but that should be really rare
			for key, val in alt_names.items():
				for alt in val:
					if alt.lower() == lowernew:
						print("WARNING: %s is a known alias of %s" % (lowernew, key))
						alt_name_risk = True
	
	if any_dups:
		if new_versions_mode:
			print("No models were added because some models have no known older version.")
		else:
			print("No models were added due to duplicates.")
		return
	
	too_long_model_names = False
	for dir in new_dirs:
		if len(dir) > 22:
			too_long_model_names = True
			print("Model name too long: %s" % dir)
			
	if too_long_model_names:
		# the game refuses to load models with long names, and servers refuse to transfer them to clients
		print("No models were added due to invalid model names.")
		return
	
	if alt_name_risk:
		x = input("\nContinue adding models even though people probably have different versions of these installed? (y/n): ")
		if x != 'y':
			return
			
	print("\n-- Lowercasing files")
	for dir in new_dirs:
		all_files = [file for file in os.listdir(os.path.join(install_path, dir))]
		mdl_files = []
		for file in all_files:
			if file != file.lower():
				src = os.path.join(install_path, dir, file)
				dst = os.path.join(install_path, dir, file.lower())
				if os.path.exists(dst):
					print("Lowercase file already exists: %s" % dst)
					sys.exit()
				else:
					print("Rename: %s -> %s" % (file, file.lower()))
				os.rename(src, dst)
		if dir != dir.lower():
			print("Rename: %s -> %s" % (dir, dir.lower()))
			os.rename(os.path.join(install_path, dir), os.path.join(install_path, dir.lower()))
	new_dirs = [dir.lower() for dir in new_dirs]
	
	if new_versions_mode:
		print("\n-- Adding version suffixes")
		renames = []
		
		versions_json = None
		with open(versions_json_name) as f:
			json_dat = f.read()
			versions_json = json.loads(json_dat, object_pairs_hook=collections.OrderedDict)
		
		for dir in new_dirs:
			found_ver = ''
			version_list_size = 1
			group_idx = -1
			for groupidx in range(0, len(versions_json)):
				group = versions_json[groupidx]
				for idx in range(0, len(group)):
					if group[idx] == dir:
						found_ver = group[0]
						version_list_size = len(group)
						group_idx = groupidx
						break
				if found_ver:
					break
			
			new_name = dir + "_v2"
			if found_ver:
				fidx = found_ver.rfind("_v")
				if fidx == -1 or not found_ver[fidx+2:].isnumeric():
					print("ERROR: Failed to find version number in %s. Don't know what to do." % new_name)
					sys.exit()
				vernum = int(found_ver[fidx+2:])
				while True:
					new_name = found_ver[:fidx] + ("_v%d" % (vernum+1))
					# TODO: this assumes all files in the database are lowercase, but shouldn't maybe
					if new_name.lower() not in old_dirs:
						break
					vernum += 1
			else:
				fidx = dir.rfind("_v")
				if fidx != -1 and dir[fidx+2:].isnumeric():
					vernum = int(dir[fidx+2])
					while True:
						new_name = dir[:fidx] + ("_v%d" % (vernum+1))
						# TODO: this assumes all files in the database are lowercase, but shouldn't maybe
						if new_name.lower() not in old_dirs:
							break
						vernum += 1
			
			old_dirs.append(new_name.lower())
			
			print("INFO: %s will be renamed to %s" % (dir, new_name))
			renames.append((dir, new_name.lower()))
			
			if group_idx != -1:
				versions_json[group_idx] = [new_name] + versions_json[group_idx]
				print("    %s" % versions_json[group_idx])
			else:
				versions_json.append([new_name.lower(), dir.lower()])
				#print("    %s" % versions_json[-1])
	
		
	
		print("\nWARNING: Proceeding will rename the above models and overwrite versions.json!")
		print("         If this process fails you will need to undo everything manually (versions.json + model names).")
		x = input("Proceed? (y/n): ")
		if x != 'y':
			return
	
		for rename_op in renames:
			rename_model(rename_op[0], rename_op[1], install_path)
			
		os.chdir(start_dir)
		
		with open(versions_json_name, 'w') as outfile:
			json.dump(versions_json, outfile, indent=4)
		print("Wrote %s" % versions_json_name)
		
		print()
		print("Restarting add process with new model names...")
		print()
		install_new_models(False)
		return
		
		# TODO: auto-update groups and tags to use latest version names
	
	print("\n-- Generating thumbnails")
	update_models(install_path, True, False, False, False, False)
	
	print("\n-- Adding %s new models" % len(new_dirs))
	for dir in new_dirs:
		src = os.path.join(install_path, dir)
		dst = os.path.join(models_path, dir)
		shutil.move(src, dst)
	
	print("\n-- Updating model list and master json")
	write_updated_models_list()
	update_models(models_path, True, True, False, False, True)
		
	print("\nFinished adding models. Next:")
	print("- python3 git_init.py update")
	print("- Update alias.json if you renamed any models")
	print("- Update groups.json and tags.json if needed")
	print("- Update replacements.json in TooManyPlugins plugin if any new")
	print("- Change the last-updated date in index.html")
	print("- git add -A; git commit; git push;")
	print("")
	print("If any model sounds were added:")
	print("- git --git-dir=.git_snd --work-tree=. add sound -f")
	print("- commit and push")
	print("")

def pack_models(all_models, lowpoly_only):
	global models_path
	
	crash_models = set()
	if os.path.exists('crash_models.txt'):
		with open(database_dir + "/crash_models.txt", "r") as update_list:
			for line in update_list.readlines():
				crash_models.add(line.lower().strip())
	
	if all_models:
		fname = 'sc_models_%s.zip' % datetime.today().strftime('%Y-%m-%d')
		cmd = 'zip -r %s models/player sound  -x "*.png" -x "*.json"' % fname
		print(cmd)
		os.system(cmd)
		# TODO: remove crash models from archive
		return
	
	add_models = []
	with open(versions_json_name) as f:
		json_dat = f.read()
		versions = json.loads(json_dat, object_pairs_hook=collections.OrderedDict)
		
		exclude = crash_models
		for group in versions:
			for idx, name in enumerate(group):
				if idx == 0:
					continue
				exclude.add(name.lower())
		
		if lowpoly_only:
			master_json = {}
			with open(master_json_name) as f:
				json_dat = f.read()
				master_json = json.loads(json_dat, object_pairs_hook=collections.OrderedDict)
				
			for model in master_json:
				if master_json[model]["polys"] > 1500:
					exclude.add(model.lower())
		
		old_dirs = get_sorted_dirs(models_path)
		all_dirs = [dir for dir in os.listdir(models_path) if os.path.isdir(os.path.join(models_path,dir)) and dir.lower() not in exclude]
		all_dirs = sorted(all_dirs, key=str.casefold)
		
		list_file = open("zip_latest.txt","w")
		for dir in all_dirs:
			for file in os.listdir(os.path.join(models_path, dir)):
				if file.endswith('.mdl') or file.endswith('.bmp') or file.endswith('.txt'):
					file_line = os.path.join(models_path, dir, file).replace('[', '\\[').replace(']', '\\]')
					list_file.write("%s\n" % file_line)
		
		sound_path = 'sound'
		all_dirs = [dir for dir in os.listdir(sound_path) if os.path.isdir(os.path.join(sound_path,dir)) and dir.lower() not in exclude]
		all_dirs = sorted(all_dirs, key=str.casefold)
		for dir in all_dirs:
			for file in os.listdir(os.path.join(sound_path, dir)):
				file_line = os.path.join(sound_path, dir, file).replace('[', '\\[').replace(']', '\\]')
				list_file.write("%s\n" % file_line)
		
		list_file.close()
		
		fname = 'models/latest_models_%s.zip' % datetime.today().strftime('%Y-%m-%d')
		cmd = 'zip %s -r . -i@zip_latest.txt' % fname
		print(cmd)
		os.system(cmd)
		os.remove("zip_latest.txt")
		
		print("\nFinished!")
		
def remove_extras():
	global models_path

	dirs = os.listdir(models_path)
	
	bad_exts = ['.smd', '.qc', '.wc', '.ztmp', '.db', '.ini', '.wav', '.ms3d', '.pe5'] # safe to delete
	img_exts = ['.bmp', '.jpg', '.tga', '.gif', '.png'] # safe to delete
	
	for dir in dirs:
		root = os.path.join(models_path, dir)
		for file in os.listdir(root):
			fpath = os.path.join(root, file)
			lowerfile = file.lower()
			mdl_name = dir
			ext = os.path.splitext(os.path.basename(file))[1].lower()
			
			if file.endswith(".mdl"):
				if file != mdl_name + ".mdl" and file != mdl_name + "t.mdl" and file != mdl_name + "01.mdl":
					print("Unexpected file: %s" % fpath)
			elif file.endswith(".txt"):
				if file != mdl_name + ".txt" and file != mdl_name + "_external.txt" and file != mdl_name + "_ragdoll.txt":
					readme_path = os.path.join(root, mdl_name + ".txt")
					if os.path.exists(readme_path):
						print("Zomg readme conflict: %s" % fpath)
					else:
						shutil.move(fpath, os.path.join(root, mdl_name + ".txt"))
						print("SET readme: %s" % fpath)
			elif file.endswith(".png"):
				if file != mdl_name + "_tiny.png" and file != mdl_name + "_small.png" and file != mdl_name + "_large.png":
					print("Unexpected file: %s" % fpath)
					#os.remove(fpath)
			elif ext in img_exts:
				if file != mdl_name + ".bmp":
					preview_path = os.path.join(root, mdl_name + ".bmp")
					if os.path.exists(preview_path):
						os.remove(fpath)
					else:
						print("Possible preview: %s" % fpath)
						#os.remove(fpath)
			elif file.endswith(".json"):
				if file != mdl_name + ".json":
					print("Unexpected file: %s" % fpath)
					#os.remove(fpath)
			elif ext in bad_exts:
				os.remove(fpath)
			else:
				print("Invalid file: %s" % fpath)
				#os.remove(fpath)

def remove_model(model_name):
	global models_path
	
	print("Removing %s" % models_path)
	
	model_path = os.path.join(models_path, model_name)
	
	if os.path.exists(model_path):
		shutil.rmtree(model_path)
		print("Deleted path: %s" % model_name)		
	
	new_versions_json = []
	with open(versions_json_name) as f:
		versions_json = json.loads(f.read(), object_pairs_hook=collections.OrderedDict)
		for arr in versions_json:
			new_arr = []
			for item in arr:
				if item != model_name:
					new_arr.append(item)
				else:
					print("Deleted %s from %s" % (model_name, versions_json_name))
			if len(new_arr):
				new_versions_json.append(new_arr)
	with open(versions_json_name, 'w') as outfile:
		json.dump(new_versions_json, outfile, indent='\t')
	
	with open(tags_json_name) as f:
		tags_json = json.loads(f.read(), object_pairs_hook=collections.OrderedDict)
		new_tags_json = {}
		for key in tags_json:
			new_tags_json[key] = []
			for item in tags_json[key]:
				if item != model_name:
					new_tags_json[key].append(item)
				else:
					print("Deleted %s from %s" % (model_name, tags_json_name))
			if len(new_tags_json[key]) == 0:
				del new_tags_json[key]
	with open(tags_json_name, 'w') as outfile:
		json.dump(new_tags_json, outfile, indent='\t')
	
	new_groups_json = {}
	with open(groups_json_name) as f:
		groups_json = json.loads(f.read(), object_pairs_hook=collections.OrderedDict)
		for key in groups_json:
			new_groups_json[key] = []
			for item in groups_json[key]:
				if item != model_name:
					new_groups_json[key].append(item)
				else:
					print("Deleted %s from %s" % (model_name, groups_json_name))
			if len(new_groups_json[key]) == 0:
				del new_groups_json[key]
	with open(groups_json_name, 'w') as outfile:
		json.dump(new_groups_json, outfile, indent='\t')
		
	new_alias_json = {}
	with open(alias_json_name) as f:
		alias_json = json.loads(f.read(), object_pairs_hook=collections.OrderedDict)
		for key in alias_json:
			new_alias_json[key] = []
			for item in alias_json[key]:
				if item != model_name:
					new_alias_json[key].append(item)
				else:
					print("Deleted %s from %s" % (model_name, alias_json_name))
			if len(new_alias_json[key]) == 0:
				del new_alias_json[key]
	with open(alias_json_name, 'w') as outfile:
		json.dump(new_alias_json, outfile, indent='\t')
			
	with open("updated.txt", 'a') as outfile:
		outfile.write("%s\n" % model_name)
	
	update_models(models_path, skip_existing=True, skip_on_error=True, errors_only=False, info_only=False, update_master_json=True)
	
	print("\nDone! Next run 'python3 git_init.py update'")

args = sys.argv[1:]

if len(args) == 0 or (len(args) == 1 and args[0].lower() == 'help'):
	print("\nUsage:")
	print("python3 scmodels.py [command]\n")
	
	print("Available commands:")
	print("update - generate thumbnails and info jsons for any new models, and updates model lists.")
	print("regen - regenerates info jsons for every model")
	print("regen_full - regenerates info jsons AND thumbnails for all models (will take hours)")
	print("rename <a> <b> - rename model <a> to <b>")
	print("rename_fast <a> <b> - skips the update so you can rename multiple models quickly.")
	print("                      but you have to remember to run update afterwards.")
	print("remove <name> - remove a model from the database")
	print("list - creates a txt file which lists every model and its poly count")
	print("dup - find duplicate files (people sometimes rename models)")
	print("add - add new models from the install folder")
	print("add_version - add new models from the install folder, but treat them as updates to models that already exist")
	print("              This will add/edit version suffixes and update versions.json.")
	print("fix_json - Makes sure tags.json and groups.json are using the latest model names, and sorts jsons.")
	print("           Run this after add_version.")
	print("pack [latest] [lowpoly] - pack all models into a zip file (default), or only the latest versions, or only low poly models")
	print("clean - remove unused files")
	
	sys.exit()

if len(args) > 0:
	if args[0].lower() == 'add':
		# For adding new models
		install_new_models(new_versions_mode=False)
	elif args[0].lower() == 'add_version':
		# For adding new models
		install_new_models(new_versions_mode=True)
	elif args[0].lower() == 'fix_json':
		# For adding new models
		fix_json()
	elif args[0].lower() == 'update':
		# For adding new models
		update_models(models_path, skip_existing=True, skip_on_error=True, errors_only=False, info_only=False, update_master_json=True)
	elif args[0].lower() == 'regen':
		update_models(models_path,skip_existing=False, skip_on_error=True, errors_only=False, info_only=True, update_master_json=True)
	elif args[0].lower() == 'regen_full':
		update_models(models_path,skip_existing=False, skip_on_error=True, errors_only=False, info_only=False, update_master_json=True)
	elif args[0].lower() == 'list':
		create_list_file()
	elif args[0].lower() == 'dup':
		find_duplicate_models(models_path)
	elif args[0].lower() == 'dup_install':
		find_duplicate_models(install_path)
	elif args[0].lower() == 'validate':
		validate_model_isolated()
	elif args[0].lower() == 'pack':
		all_models = True
		lowpoly_only = False
		if len(args) > 1 and args[1].lower() == "latest":
			all_models = False
		if len(args) > 2 and args[2].lower() == "lowpoly":
			lowpoly_only = True
			
		pack_models(all_models, lowpoly_only)
	elif args[0].lower() == 'rename':
		print("TODO: Add to alias after rename")
		rename_model(args[1], args[2], models_path)
		os.chdir(start_dir)
		update_models(models_path, skip_existing=True, skip_on_error=True, errors_only=False, info_only=True, update_master_json=True)
		list_file = open("updated.txt","w") 
		list_file.write("%s\n" % args[1])
		list_file.write("%s\n" % args[2])
		list_file.close()
		print("\nFinished rename. Next:")
		print("- update name in groups.json (TODO: automate)")
		print("- update name in versions.json")
		print("- python3 git_init.py update")
		print("- push changes to main repo")
	elif args[0].lower() == 'rename_fast':
		print("TODO: Add to alias after rename")
		rename_model(args[1], args[2], models_path)
		os.chdir(start_dir)
		list_file = open("updated.txt","a") 
		list_file.write("%s\n" % args[1])
		list_file.write("%s\n" % args[2])
		list_file.close()
	elif args[0].lower() == 'remove':
		remove_model(args[1])
	elif args[0].lower() == 'clean':
		remove_extras()
	elif args[0].lower() == 'fixup':
		pass
	
		'''
		new_dirs = get_sorted_dirs(install_path)
	
		old_dirs = [dir for dir in os.listdir(models_path) if os.path.isdir(os.path.join(models_path,dir))]
		old_dirs_lower = [dir.lower() for dir in old_dirs]

		for dir in new_dirs:
			#if not os.path.exists(os.path.join(models_path, dir + '_v2')):
			#	continue
			if os.path.exists(os.path.join(models_path, dir + '_v2')):
				continue
				
			lowernew = dir.lower()
			for idx, old in enumerate(old_dirs):
				if lowernew == old.lower():
					newDate = get_model_modified_date(dir, install_path)
					oldDate = get_model_modified_date(dir, models_path)
					
					diff = "NEWER" if oldDate > newDate else "OLDER"
					
					if oldDate < newDate:
						#print("RENAME " + dir)
						#rename_model(dir, dir + "_v2", install_path)
						#os.chdir(start_dir)
						#break
						pass
					
					print("ERROR: %s already exists (%s)" % (old, diff))
					any_dups = True
					#rename_model(old, old + "_v2", models_path)
		'''
	else:
		print("Unrecognized command. Run without options to see help")

#update_models(skip_existing=True, errors_only=False)

#check_for_broken_models()
#get_lowest_polycount()