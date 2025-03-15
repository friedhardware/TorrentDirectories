# Changelog

## 0.5.0 (2025-03-15)

* docs: clarify release process and fix test dependencies installation command
* feat: enhance release process with automated changelog and version management
* add release scripts.
* Release v0.4.0
* chore: add development dependencies including setuptools
* refactor: complete migration from core.py to torrent_creator.py
* refactor: rename core.py to torrent_creator.py for better clarity
* Update process_batch parameter order and docstring
* Add table of contents to README for better navigation
* Update README to reflect process_batch argument order and default output directory
* Set default output directory to 'torrents/' - Add default output directory for batch processing - Update tests to use and verify default directory - Remove unnecessary output_dir checks
* Rename create_torrent to create for better readability - Remove redundant 'torrent' from method name since TorrentCreator provides context - Update all references and tests to use new method name
* Clean up unused imports across codebase - Remove unused imports from manifest.py, file_utils.py, config.py, test files - Improve code cleanliness and reduce dependencies
* Improve manifest handling and dry run output - Update dry run output in batch mode, fix manifest CSV quoting, add tests
* update .gitignore
* ddtogitignore
* remove .dsstore
* chore: add .DS_Store to gitignore
* fix(manifest): correct manifest configuration handling
* feat(torrent): set default minimum piece size to 256 KiB
* feat(torrent): reduce minimum piece size to 16 KiB
* feat(torrent): enforce 64 MiB maximum piece size limit
* Enhance CLI documentation with comprehensive examples and options
* Add virtual environment setup to installation instructions
* Add coverage files to .gitignore
* Refactor project structure and add test framework: reorganize into proper Python package, add test suite, config files, and update docs
* Enhance torrent_utils.py with improved type safety and error handling
* Simplify manifest validation to single yes/no choice for handling discrepancies
* Update README: Document CSV manifest format, improve validation state descriptions, add examples
* Improve manifest handling: Add thorough validation, include torrent filename in skip messages, remove unused save_manifest function
* Update prerequisite section with clear installation steps for libtorrent bindings
* Improve output directory naming and update documentation
* Initial commit: Torrent creation tool with optimal piece size calculation
## 0.4.0 (2024-03-15)

* add release scripts
* chore: add development dependencies including setuptools
* refactor: complete migration from core.py to torrent_creator.py
* refactor: rename core.py to torrent_creator.py for better clarity
* Update process_batch parameter order and docstring
* Add table of contents to README for better navigation
* Update README to reflect process_batch argument order and default output directory
* Set default output directory to 'torrents/'
  - Add default output directory for batch processing
  - Update tests to use and verify default directory
  - Remove unnecessary output_dir checks
* Rename create_torrent to create for better readability
  - Remove redundant 'torrent' from method name since TorrentCreator provides context
  - Update all references and tests to use new method name
* Clean up unused imports across codebase
  - Remove unused imports from manifest.py, file_utils.py, config.py, test files
  - Improve code cleanliness and reduce dependencies
* Improve manifest handling and dry run output
  - Update dry run output in batch mode
  - Fix manifest CSV quoting
  - Add tests

## 0.3.0 (2024-03-14)

* update .gitignore
* ddtogitignore
* remove .dsstore
* chore: add .DS_Store to gitignore
* fix(manifest): correct manifest configuration handling
* feat(torrent): set default minimum piece size to 256 KiB
* feat(torrent): reduce minimum piece size to 16 KiB
* feat(torrent): enforce 64 MiB maximum piece size limit
* Enhance CLI documentation with comprehensive examples and options
* Add virtual environment setup to installation instructions
* Add coverage files to .gitignore

## 0.2.0 (2024-03-13)

* Refactor project structure and add test framework
  - Reorganize into proper Python package
  - Add test suite
  - Add config files
  - Update docs
* Enhance torrent_utils.py with improved type safety and error handling
* Simplify manifest validation to single yes/no choice for handling discrepancies
* Update README
  - Document CSV manifest format
  - Improve validation state descriptions
  - Add examples
* Improve manifest handling
  - Add thorough validation
  - Include torrent filename in skip messages
  - Remove unused save_manifest function
* Update prerequisite section with clear installation steps for libtorrent bindings
* Improve output directory naming and update documentation

## 0.1.0 (2024-03-12)

* Initial commit: Torrent creation tool with optimal piece size calculation 