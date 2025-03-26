from cbz_tagger.container.container import get_arg_parser, run_container

kwargs = get_arg_parser()
run_container(**kwargs)
