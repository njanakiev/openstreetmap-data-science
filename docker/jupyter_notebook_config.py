import os
c = get_config()

# Kernel config
c.IPKernelApp.pylab = 'inline'  # if you want plotting support always in your notebook

# Notebook config
c.ServerApp.root_dir = '/workspace'
c.ServerApp.ip = '*'
c.ServerApp.allow_remote_access = True
c.ServerApp.open_browser = False
c.ServerApp.password = 'sha1:ee1d9c17d856:8e206189ec9d5afb31e8fb7422ac09778c5a105f'
c.ServerApp.port = 8888
c.ServerApp.allow_root = True
c.ServerApp.allow_password_change = True

# ContentsManager
c.ContentsManager.allow_hidden = True
