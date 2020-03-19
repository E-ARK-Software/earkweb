from configparser import ConfigParser

from eatb.utils.randomutils import randomword


def set_default_config_if_not_exists(cfg_file, default_cfg):
    config = ConfigParser()
    config.read(cfg_file)
    changed = False
    for conf in default_cfg:
        section, option, value = conf
        if not config.has_section(section):
            config.add_section(section)
        try:
            config.get(section, option)
        except Exception:
            print("Adding missing configuration option with default values: section: %s, option: %s, value: %s" % (
            section, option, value))
            config.set(section, option, value)
            changed = True

    if changed:
        with open(cfg_file, 'w') as fp:
            config.write(fp)
        print("Config file written: %s" % cfg_file)


if __name__ == "__main__":
    config_file = "/tmp/configexample%s.cfg" % randomword(5)
    default_config = [
        ("newsection", "example_a", "foo"),
        ("newsection", "example_b", 1),
        ("newsection", "example_c", "bar"),
    ]
    set_default_config_if_not_exists(config_file, default_config)
