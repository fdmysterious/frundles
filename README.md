# Frundles

[![PyPI - Version](https://img.shields.io/pypi/v/frundles.svg)](https://pypi.org/project/frundles)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/frundles.svg)](https://pypi.org/project/frundles)

- Florian Dupeyron &lt;florian.dupeyron@mugcat.fr&gt;
- August 2024

Frundles is a simple tool to manage git repos for FPGA/HDL related projects.

![Frundles logo](./docs/assets/img/logo-frundles.svg)

## Usage

### Installation

Last version can be installed from `pip`:

```
pip install frundles
```


### Main configuration file

A file named `frundles.yml` can be put at the root of your repository. Here is some template code for this file:


```yml
workspace:
    catalog_dir: 'ip'
    mode: 'recurse'

libraries:
    - origin: 'https://github.com/stnolting/neorv32.git'
      tag: 'v1.10.6'
      friendly_name: 'neorv32'

    - origin: 'https://github.com/pulp-platform/common_cells.git'
      tag: 'v1.37.0'
      friendly_name: 'pulp-common_cells'

    - origin: 'https://github.com/pulp-platform/tech_cells_generic.git'
      tag: 'v0.2.13'
      friendly_name: 'pulp-tech_cells_generic'

    - origin: 'https://github.com/pulp-platform/fpu_ss.git'
      branch: 'main'
      friendly_name: 'pulp-fpu_ss'
```


### Basic commands

#### `frundles sync`

Calling this commands synchronizes your work directory with remote content.

For instance, with the above configuration file, here is the folder before the `frundles sync` command:

```
.
└── frundles.yml
```

Running the command should give this kind of output:

```
$ ~/workspace/frundles-tutorial  
> frundles sync
2024-11-04 23:45:39 <hostname> frundles[10529] INFO Hello world!
2024-11-04 23:45:39 <hostname> frontend.sync[10529] INFO Synchronize workspace located in /home/<user>/workspace/frundles-tutorial
2024-11-04 23:45:39 <hostname> backend.workspace[10529] INFO Load workspace information from /home/<user>/workspace/frundles-tutorial
2024-11-04 23:45:39 <hostname> backend.workspace[10529] INFO Syncing workspace located at /home/<user>/workspace/frundles-tutorial, using mode 'recurse'
2024-11-04 23:45:39 <hostname> backend.catalog[10529] INFO Check for /home/<user>/workspace/frundles-tutorial/ip as a catalog folder
2024-11-04 23:45:39 <hostname> backend.catalog[10529] WARNING /home/<user>/workspace/frundles-tutorial/ip doesn't exist yet, creating the folder
2024-11-04 23:45:39 <hostname> backend.workspace[10529] INFO Attempt to sync library lib:neorv32:v1.10.6
2024-11-04 23:45:39 <hostname> backend.workspace[10529] WARNING lib:neorv32:v1.10.6 is not locked, resolve commit
2024-11-04 23:46:05 <hostname> backend.workspace[10529] INFO Resolved commit to f9a2801c5c5764f26e57867ee67d7a6eebbd941b, saving to lock file /home/<user>/workspace/frundles-tutorial/frundles.lock
2024-11-04 23:46:05 <hostname> backend.workspace[10529] INFO Clone lib:neorv32:v1.10.6 library to /home/<user>/workspace/frundles-tutorial/ip/neorv32
2024-11-04 23:46:31 <hostname> backend.workspace[10529] INFO Attempt to sync library lib:common_cells:v1.37.0
2024-11-04 23:46:31 <hostname> backend.workspace[10529] WARNING lib:common_cells:v1.37.0 is not locked, resolve commit
2024-11-04 23:46:32 <hostname> backend.workspace[10529] INFO Resolved commit to c27bce39ebb2e6bae52f60960814a2afca7bd4cb, saving to lock file /home/<user>/workspace/frundles-tutorial/frundles.lock
2024-11-04 23:46:32 <hostname> backend.workspace[10529] INFO Clone lib:common_cells:v1.37.0 library to /home/<user>/workspace/frundles-tutorial/ip/pulp-common_cells
2024-11-04 23:46:32 <hostname> backend.workspace[10529] INFO Attempt to sync library lib:tech_cells_generic:v0.2.13
2024-11-04 23:46:32 <hostname> backend.workspace[10529] WARNING lib:tech_cells_generic:v0.2.13 is not locked, resolve commit
2024-11-04 23:46:34 <hostname> backend.workspace[10529] INFO Resolved commit to 7968dd6e6180df2c644636bc6d2908a49f2190cf, saving to lock file /home/<user>/workspace/frundles-tutorial/frundles.lock
2024-11-04 23:46:34 <hostname> backend.workspace[10529] INFO Clone lib:tech_cells_generic:v0.2.13 library to /home/<user>/workspace/frundles-tutorial/ip/pulp-tech_cells_generic
2024-11-04 23:46:35 <hostname> backend.workspace[10529] INFO Attempt to sync library lib:fpu_ss:main
2024-11-04 23:46:35 <hostname> backend.workspace[10529] WARNING lib:fpu_ss:main is not locked, resolve commit
2024-11-04 23:46:36 <hostname> backend.workspace[10529] INFO Resolved commit to 809e9a63e3b627f4908ba4189ed26bbf7209ba25, saving to lock file /home/<user>/workspace/frundles-tutorial/frundles.lock
2024-11-04 23:46:36 <hostname> backend.workspace[10529] INFO Clone lib:fpu_ss:main library to /home/<user>/workspace/frundles-tutorial/ip/pulp-fpu_ss
```

And the repository should look like this afterwards:

```
├── frundles.lock
├── frundles.yml
└── ip
    ├── neorv32
    │   └── <files from the neorv32 repo>
    ├── pulp-common_cells
    │   └── <files from the pulp common_cells repo>
    ├── pulp-fpu_ss
    │   └── <files from the pulp fpu_ss repo>
    └── pulp-tech_cells_generic
        └── <files from the pulp tech_cells_generic repo>
```

The `frundles.lock` file caches the commit ID associated with the providen reference:

```
lib:common_cells:tag:v1.37.0:c27bce39ebb2e6bae52f60960814a2afca7bd4cb
lib:neorv32:tag:v1.10.6:f9a2801c5c5764f26e57867ee67d7a6eebbd941b
lib:fpu_ss:branch:main:809e9a63e3b627f4908ba4189ed26bbf7209ba25
lib:tech_cells_generic:tag:v0.2.13:7968dd6e6180df2c644636bc6d2908a49f2190cf
```

This ensure reproducability given a repo. For instance, if working on a development branch, this freezes the configuration at any given moment. The corresponding commit reference of a development branch can be updated to last revision using the `frundles bump` command.

If any remo has been modified locally or doesn't target the right commit, warning messages can be issued.


#### `frundles list` command

The `frundles list` command shows the list of configured dependencies for the current workspace.

```
$ ~/workspace/frundles-tutorial  
> frundles list
2024-11-04 23:52:42 <hostname> frundles[10914] INFO Hello world!
2024-11-04 23:52:42 <hostname> backend.workspace[10914] INFO Search workspace file starting from /home/<user>/workspace/frundles-tutorial
2024-11-04 23:52:42 <hostname> backend.workspace[10914] INFO Load workspace information from /home/<user>/workspace/frundles-tutorial
2024-11-04 23:52:42 <hostname> backend.workspace[10914] INFO Found lockfile for workspace /home/<user>/workspace/frundles-tutorial at /home/<user>/workspace/frundles-tutorial/frundles.lock

Available libraries:

| Reference                      | Friendly name           |
|--------------------------------|-------------------------|
| lib:neorv32:v1.10.6            | neorv32                 |
| lib:common_cells:v1.37.0       | pulp-common_cells       |
| lib:tech_cells_generic:v0.2.13 | pulp-tech_cells_generic |
| lib:fpu_ss:main                | pulp-fpu_ss             |
```


#### `frundles bump` command

The `frundles bump` command can be used to update a specific library to its latest revision if it targets a development branch.

For instance, if the `pulp-fpu_ss` doesn't point to the last commit:

```
> frundles bump pulp-fpu_ss
2024-11-05 00:00:54 <hostname> frundles[11243] INFO Hello world!
2024-11-05 00:00:54 <hostname> backend.workspace[11243] INFO Search workspace file starting from /home/<user>/workspace/frundles-tutorial
2024-11-05 00:00:54 <hostname> backend.artifact[11243] WARNING Repo in '/home/<user>/workspace/frundles-tutorial' has no 'origin' remote URL, assuming local directory path
2024-11-05 00:00:54 <hostname> backend.workspace[11243] INFO Load workspace information from /home/<user>/workspace/frundles-tutorial
2024-11-05 00:00:54 <hostname> backend.workspace[11243] INFO Found lockfile for workspace /home/<user>/workspace/frundles-tutorial at /home/<user>/workspace/frundles-tutorial/frundles.lock
2024-11-05 00:00:54 <hostname> backend.workspace[11243] INFO Attempt to sync library lib:fpu_ss:main
2024-11-05 00:00:54 <hostname> backend.workspace[11243] INFO Bump requested for lib:fpu_ss:main, check most recent revision
2024-11-05 00:00:55 <hostname> backend.workspace[11243] INFO Save new refspec for lib:fpu_ss:main to lockfile /home/<user>/workspace/frundles-tutorial/frundles.lock
```

Then the diff on `frundles.lock` file shows the change for the `pulp-fpu_ss` library:

```
$ ~/workspace/frundles-tutorial  
> git diff frundles.lock 
diff --git a/frundles.lock b/frundles.lock
index 73907c9..70755b3 100644
--- a/frundles.lock
+++ b/frundles.lock
@@ -1,4 +1,4 @@
 lib:common_cells:tag:v1.37.0:c27bce39ebb2e6bae52f60960814a2afca7bd4cb
-lib:neorv32:tag:v1.10.6:f9a2801c5c5764f26e57867ee67d7a6eebbd941b
-lib:fpu_ss:branch:main:1731e34ae7fd07512b9e4077f922d18f46d0fe24
 lib:tech_cells_generic:tag:v0.2.13:7968dd6e6180df2c644636bc6d2908a49f2190cf
+lib:neorv32:tag:v1.10.6:f9a2801c5c5764f26e57867ee67d7a6eebbd941b
+lib:fpu_ss:branch:main:809e9a63e3b627f4908ba4189ed26bbf7209ba25
```


#### `frundles bump-all` command

The `frundles bump-all` command is like the `bump` command, but for all libraries at once.


## Development

### Tools

The project uses the following tools:

- hatch: project management, virtual environment, packaging tools;
- pre-commit: quality assurance for repo focusing on developer experience (DX).

You can install these tools (one time only) using pip:

```
pip install hatch pre-commit
```

The first time you checkout the repository, make sure to configure `pre-commit` properly:

```
pre-commit install
```

### Environments

This project makes an extensive use of hatch's "environments" fulfilling various needs:

#### `docs` environment

This environment allow to build the project's documentation using `mkdocs`. To build the project documentation, simply run:

```
hatch run docs:build
```

Generated documentation shall be available in the `site` output folder.


#### `types` environment

This auxiliary environment uses `mypy` for type checking.

You can run the type checker using:

```
hatch run types:check
```


#### `lint` environment

This environment contains the `ruff` linter as well as the `black` formatter. These shall be already run by `pre-commit` when comitting to the repository.

Behind the scenes, the `pre-commit` hooks makes use of the following commands:

- Lint the code using `ruff`: `hatch run lint:code-rules`
- Format the code using `black`: `hatch run lint:code-format`
