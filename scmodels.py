import sys, os, shutil, collections, json, subprocess, stat, hashlib, traceback, time
from glob import glob
from io import StringIO

# TODO:
# - some models I added _v2 to are actually a completely different model
# - delete all thumbs.db and .ztmp
# - lowercase before adding new models

master_json = {}
master_json_name = 'models.json'

alias_json_name = 'alias.json'

start_dir = os.getcwd()

models_path = 'models/player/'
install_path = 'install/'
hlms_path = os.path.join(start_dir, 'hlms')
posterizer_path = '/home/pi/mediancut-posterizer/posterize'
pngcrush_path = 'pngcrush'
magick_path = 'convert'
debug_render = False


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
	return time.ctime(os.path.getmtime(mdl_path))

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
	global hlms_path
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
	global hlms_path
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
			try:
				args = [hlms_path, './' + mdl_path]
				output = subprocess.check_output(args)
			except Exception as e:
				output = e
				print(e)
				print("Bad model: %s" % model_name)
		else:
			print("Missing model: %s" % model_name)

def generate_info_json(model_name, mdl_path, output_path):
	data = {}
	output = ''
	try:
		args = [hlms_path, './' + mdl_path]
		output = subprocess.check_output(args)
	except Exception as e:
		output = e
		print(e)
			
	output = StringIO(output.decode('utf-8'))
	
	t_model_file = None
	begin_parse = False
	for line in output:
		line = line.replace('\n', '')
		if line == '!BEGIN_MODEL_INFO!':
			begin_parse = True
			continue
		if line == '!END_MODEL_INFO!':
			break
		if not begin_parse:
			continue
		keyvalue = line.split("=")
		if len(keyvalue) != 2:
			print("Invalid keyvalue: %s" % line)
			continue
		key = keyvalue[0]
		value = keyvalue[1]
		if key in ['sequences', 'event']:
			value = value.split("|")
		
		if key == 't_model':
			if value == '1' or value == 1:
				found_t_model = False
				all_files = [file for file in os.listdir('.') if os.path.isfile(file)]
				t_model_name = model_name + "t.mdl"
				for file in all_files:
					if file.lower() == t_model_name.lower():
						data['t_model'] = t_model_file = file
						found_t_model = True
						break
				if not found_t_model:
					print("Missing T Model: %s" % t_model_name)
					raise Exception('Missing T Model')
		
		elif key == 'seq_groups':
			if value != '1':
				for i in range(0, int(value)):
					suffix = "%s" % (i+1)
					if i < 10:
						suffix = "0" + suffix
					path = model_name + suffix + ".mdl"
					if not os.path.exists(path):
						print("Missing animation model: %s" % path) # not always fatal, but could be
			data['seq_groups'] = int(value)
			
		elif key == 'event':
			value = {
				'seq': value[0],
				'frame': value[1],
				'file': value[2]
			}
			if 'events' not in data:
				data['events'] = []
			data['events'].append(value)
		else:
			data[key] = value
		#print("Save key %s" % key)
		
	data['hash'] = hash_md5(mdl_path, t_model_file)
		
	with open(output_path, 'w') as outfile:
		json.dump(data, outfile)

def update_models(work_path, skip_existing=True, skip_on_error=False, errors_only=True, info_only=False, update_master_json=False):
	global master_json
	global magick_path
	global pngcrush_path
	global posterizer_path
	global hlms_path
	global start_dir
	
	all_dirs = get_sorted_dirs(work_path)
	total_dirs = len(all_dirs)
	
	#list_file = open("updated.txt","w") 
	failed_models = []
	
	for idx, dir in enumerate(all_dirs):
		model_name = dir
		print("IDX: %s / %s: %s                  " % (idx, total_dirs-1, model_name), end='\r')
		
		#garg.mdl build/asdf 1000x1600 0 1 1
		
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
		sequence = "0"
		frames = "1"
		loops = "1"
		
		info_json_path = model_name + ".json"
		tiny_thumb = model_name + "_tiny.png"
		small_thumb = model_name + "_small.png"
		large_thumb = model_name + "_large.png"
		
		thumbnails_generated = os.path.isfile(tiny_thumb) and os.path.isfile(small_thumb) and os.path.isfile(large_thumb)
		
		anything_updated = False
		
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
					args = [hlms_path, mdl_path, model_name, "1000x1600", sequence, frames, loops]
					null_stdout=None if debug_render else devnull
					subprocess.check_call(args, stdout=null_stdout)

					def create_thumbnail(name, size, posterize_colors):
						print("Creating %s thumbnail..." % name)
						temp_path = "./%s_%s_temp.png" % (model_name, name)
						final_path = "./%s_%s.png" % (model_name, name)
						subprocess.check_call([magick_path, "./" + render_path, "-resize", size, temp_path], stdout=null_stdout)
						subprocess.check_call([posterizer_path, posterize_colors, temp_path, final_path], stdout=null_stdout)
						subprocess.check_call([pngcrush_path, "-ow", "-q", final_path], stdout=null_stdout)
						os.remove(temp_path)

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
			anything_updated = False
			if not skip_on_error:
				sys.exit()
				
		#if anything_updated:
		#	list_file.write("%s\n" % model_name)
		#	print("")
	
		os.chdir(start_dir)
		
		if update_master_json:
			master_json[model_name] = {}
			
	if update_master_json:
		with open(master_json_name, 'w') as outfile:
			json.dump(master_json, outfile)
		
	#list_file.close()
	
	print("\nFinished!")
	
	if len(failed_models):
		print("\nFailed to update these models:")
		for fail in failed_models:
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
	hlmsPath = os.path.join(boxPath, "hlms")
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
	global hlms_path
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
				hash = dat['hash']
				
				if hash not in model_hashes:
					model_hashes[hash] = [model_name]
				else:
					model_hashes[hash].append(model_name)
		else:
			print("\nMissing info JSON for %s" % model_name)
			
	print("Progress: %d / %d" % (len(all_dirs), len(all_dirs)))
	os.chdir(start_dir)
	
	return model_hashes

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

def install_new_models():
	global models_path
	global install_path
	global alias_json_name
	
	new_dirs = get_sorted_dirs(install_path)
	if len(new_dirs) == 0:
		print("No models found in %s" % install_path)
		sys.exit()
	
	alt_names = {}
	if os.path.exists(alias_json_name):
		with open(alias_json_name) as f:
			json_dat = f.read()
			alt_names = json.loads(json_dat, object_pairs_hook=collections.OrderedDict)
	
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
	
	model_hashes = load_all_model_hashes(models_path)
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
	
	with open(alias_json_name, 'w') as outfile:
		json.dump(alt_names, outfile)
	
	if len(dups) > 0 and input("\nDelete the duplicate models in the install folder? (y/n)") == 'y':
		for dup in dups:
			path = os.path.join(install_path, dup)
			shutil.rmtree(path)
	
	old_dirs = [dir for dir in os.listdir(models_path) if os.path.isdir(os.path.join(models_path,dir))]
	old_dirs_lower = [dir.lower() for dir in old_dirs]
	
	for dir in new_dirs:
		lowernew = dir.lower()
		for idx, old in enumerate(old_dirs):
			if lowernew == old.lower():
				print("ERROR: %s already exists" % old)
				rename_model(old, old + "_v2", models_path)
			
	
	if any_dups:
		print("No models were added due to duplicates.")
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
		
	print("Finished.")

args = sys.argv[1:]

if len(args) == 0 or (len(args) == 1 and args[0].lower() == 'help'):
	print("\nUsage:")
	print("sudo python3 scmodels.py [command]\n")
	
	print("Available commands:")
	print("update - generate thumbnails and info jsons for any models.")
	print("regen - regenerates info jsons for every model")
	print("regen_full - regenerates info jsons AND thumbnails for all models (will take hours)")
	print("rename <a> <b> - rename model <a> to <b>")
	print("list - creates a txt file which lists every model and its poly count")
	print("dup - find duplicate files (people sometimes rename models)")
	print("add - add new models from the install folder")
	
	sys.exit()

if len(args) > 0:
	if args[0].lower() == 'add':
		# For adding new models
		install_new_models()
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
	elif args[0].lower() == 'rename':
		rename_model(args[1], args[2], models_path)
		os.chdir(start_dir)
		update_models(models_path, skip_existing=True, skip_on_error=True, errors_only=False, info_only=True, update_master_json=True)
		list_file = open("updated.txt","w") 
		list_file.write("%s\n" % args[1])
		list_file.write("%s\n" % args[2])
		list_file.close()
		print("\nNow run:")
		print("python3 git_init.py update")
		print("then push changes to main repo")
	else:
		print("Unrecognized command. Run without options to see help")

#update_models(skip_existing=True, errors_only=False)

#check_for_broken_models()
#get_lowest_polycount()