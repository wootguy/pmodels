# pmodels

A faster way to find player models.

Website:  
https://wootguy.github.io/pmodels/

Model repos:  
https://github.com/wootdata?tab=repositories

Model viewer, thumbnail generator, JSON exporter:  
https://github.com/wootguy/modelguy

# API to download models
If you want to download models from this database in your own project, follow steps below. It's complicated because the data is split up into many repos.

1) Download one of these files to get all available model names:  
  https://github.com/wootguy/pmodels/blob/master/database/hl/model_names.txt (Half-Life)  
  https://github.com/wootguy/pmodels/blob/master/database/sc/model_names.txt (Sven Co-op)
1) Plug a model name into the function below to get its data repository url. 
  https://github.com/wootguy/pmodels/blob/7aec5c8b92038276badebbd05626c98de1bda31b/modeldb.js#L881-L896
  `data_repo_domain` is `https://wootdata.github.io/` for my instance of the database.  
  `g_game_id` can either be `hl` for Half-Life or `sc` for Sven co-op.
1) Add the file path to the url in step 2 get what you want. For example, if you're downloading the `betagordon` model:  
  `models/player/betagordon/betagordon.mdl` = The model file  
  `models/player/betagordon/betagordon.bmp` = The preview image  
  `models/player/betagordon/betagordon.json` = Metadata for the model. This tells you if there are external models (*T.mdl, *01.mdl), animation sounds, or a readme file. I'm pretty sure I've removed or merged all models that use external models so this is an optional step.

Example code for downloading everything linked to a model:
https://github.com/wootguy/pmodels/blob/7aec5c8b92038276badebbd05626c98de1bda31b/modeldb.js#L368
  
  
