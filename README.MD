<div align="center">
  <a href="https://github.com/Reloaded-Project/rust-lightweight-binary" target="_blank">
    <img src="assets/reloaded-logo.png" alt="reloaded Logo" width="100"/>
  </a>

  <h1 align="center">Reloaded Rust Build C Library Workflow</h1>

  <p>
    <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License">
    </a>
  </p>
</div>

This is a GitHub Action that can be used to build an optimized, lightweight binary (or C library)
from a Rust project.

This action is used to build binaries with the following properties:

- **Self-Built std**: Reduces binary size and improves optimizations.
- **Abort on Panic**: Reduces binary size. Can be disabled if needed.
- **Profile Guided Optimization (PGO)**: Improves performance by optimizing based on usage patterns.
- **Cross-Compilation**: Supports cross-compilation using `cross-rs`.
- **Nightly Rust**: Uses the nightly Rust toolchain for building and running.
- **Tests and Coverage**: Optionally run tests and generate coverage reports using the `devops-rust-test-and-coverage` action.

It can be used to build both binaries and C libraries.

## Example Usage

As a single job/step of a workflow:

```yaml
test-binary-build:
  strategy:
    matrix:
      include:
        - os: ubuntu-latest
          target: x86_64-unknown-linux-gnu
          use-pgo: true
          use-cross: false
        - os: ubuntu-latest
          target: i686-unknown-linux-gnu
          use-pgo: true
          use-cross: false
        - os: ubuntu-latest
          target: aarch64-unknown-linux-gnu
          use-pgo: false # no native runner
          use-cross: true
        - os: ubuntu-latest
          target: armv7-unknown-linux-gnueabihf
          use-pgo: false # no native runner
          use-cross: true
        - os: windows-latest
          target: x86_64-pc-windows-msvc
          use-pgo: true
          use-cross: false
        - os: windows-latest
          target: i686-pc-windows-msvc
          use-pgo: true
          use-cross: false
        - os: windows-latest
          target: aarch64-pc-windows-msvc
          use-pgo: false # no native runner
          use-cross: false
        - os: macos-13 # x86
          target: x86_64-apple-darwin
          use-pgo: true
          use-cross: false
        - os: macos-14 # M1
          target: aarch64-apple-darwin
          use-pgo: true
          use-cross: false
  runs-on: ${{ matrix.os }}
  steps:
    - name: Checkout Test Repository
      uses: actions/checkout@v4
      with:
        repository: Sewer56/prs-rs
        ref: d08599ed5473616f57d57a0966939e1a5dbda9b4
    - name: Test Binary Build
      uses: Reloaded-Project/devops-rust-lightweight-binary@v1
      with:
        target: ${{ matrix.target }}
        use-pgo: ${{ matrix.use-pgo }}
        use-cross: ${{ matrix.use-cross }}
        rust-project-path: "tools/cli/"
        crate-name: "prs-rs-cli"
        upload-artifacts: false
        run-tests-and-coverage: true
```

## Setup

To use this action in your own repository:

1. Create a new workflow file (e.g., `.github/workflows/build-c-library.yml`) in your repository.
2. Copy the example usage job from above into the new workflow file.
3. Customize the input parameters as needed for your project.

## Configuration

### Inputs

| Input                        | Required | Default          | Description                                                                            |
| ---------------------------- | -------- | ---------------- | -------------------------------------------------------------------------------------- |
| `rust-project-path`          | No       | `.`              | Path to the Rust project                                                               |
| `pgo-project-path`           | No       | `.`              | Path to the Rust project used for gathering PGO data. Can be same or separate project. |
| `crate-name`                 | Yes      |                  | Name of the Rust crate (used to determine file name)                                   |
| `target`                     | Yes      |                  | The target platform for the Rust compiler                                              |
| `features`                   | No       | `''`             | Comma-separated list of features to include in the build                               |
| `no-default-features`        | No       | `false`          | Do not include default features in the build                                           |
| `use-pgo`                    | No       | `false`          | Use Profile-Guided Optimization [PGO] to build the library.                            |
| `pgo-benchmark-name`         | No       | `'my_benchmark'` | Benchmark name to use with PGO.                                                        |
| `use-cross`                  | No       | `false`          | Use cross-rs for building. If false, use cargo.                                        |
| `additional-rustflags`       | No       | `''`             | Additional RUSTFLAGS to pass to the Rust compiler                                      |
| `upload-artifacts`           | No       | `true`           | Upload the built artifacts as a GitHub Actions artifact                                |
| `abort-on-panic`             | No       | `true`           | Abort immediately on panic. If false, the default panic handler is used.               |
| `build-library`              | No       | `false`          | Build a library instead of a binary.                                                   |
| `run-tests-and-coverage`     | No       | `false`          | Run tests and coverage using the `devops-rust-test-and-coverage` action.               |
| `upload-coverage-to-codecov` | No       | `true`           | Uploads coverage to codecov if `run-tests-and-coverage` is enabled.                    |

### Setting up Profile-Guided Optimization (PGO)

Profile-Guided Optimization works by compiling and executing a benchmark whose name and project
can be defined by `pgo-benchmark-name` and `pgo-project-path` respectively. So you should strive
to keep the benchmark as close to the final usage of your application as possible.

A benchmark for PGO can be defined as follows:

```rust
// Regular benchmarks, not PGO
#[cfg(not(feature = "pgo"))]
{
    bench_estimate(c);
    bench_decompress(c);
    bench_compress_file(c);
    bench_create_dict(c);
}

// Benchmark with realistic usage patterns for PGO.
#[cfg(feature = "pgo")]
{
    generate_pgo_data();
}
```

Then said profile is used to build the final version of your application.

For PGO to work, the `target` platform must be the same as the host that generated the profiling
data. Sometimes you can get away with using `cross` to achieve this, for example:

```yaml
# Host is x86-linux but this seems to work just a-ok!
target: aarch64-unknown-linux-gnu # x64 host to to aarch64 simulated guest
use-pgo: true
use-cross: true
```

If the process fails, your CI will fail, so do experiment.

## Running Tests and Coverage

To run tests and generate coverage reports as part of the build process, set the
`run-tests-and-coverage` input to `true`.

This will invoke the [devops-rust-test-and-coverage][devops-test-coverage] action after the build
step, using the same configuration as the build (e.g., `target`, `features`, `use-cross`, etc.).

The `devops-rust-test-and-coverage` action will run tests using either `cargo` or `cross`,
depending on the `use-cross` input. If `use-cross` is `false`, it will also generate a coverage
report using Tarpaulin and upload it to Codecov (if `upload-coverage` is `true`).

Note that code coverage is skipped when using `cross` due to incompatibility with Tarpaulin.

## Building Libraries

To build a library instead of a binary, set the `build-library` input to `true`.
This is equivalent to setting `crate-type = ["cdylib", "staticlib"]` in `Cargo.toml`.

When building a library, the generated artifacts will include static libraries (`.a`, `.lib`) 
and dynamic libraries (`.so`, `.dll`, `.dylib`) depending on the target platform.

## Examples

Find more examples in [the tests](./.github/workflows/test-rust-build-c-library-workflow.yml).

### Custom PGO Project Path

```yaml
- name: Build C Library
  uses: Reloaded-Project/devops-rust-lightweight-binary@v1
  with:
    rust-project-path: ./rust-project
    pgo-project-path: ./pgo-project
    crate-name: my-crate
    target: x86_64-unknown-linux-gnu
```

### Using cross-rs for Building

```yaml
- name: Build C Library
  uses: Reloaded-Project/devops-rust-lightweight-binary@v1
  with:
    crate-name: my-crate
    target: x86_64-unknown-linux-gnu
    use-cross: true
```

### Custom Additional RUSTFLAGS

```yaml
- name: Build C Library
  uses: Reloaded-Project/devops-rust-lightweight-binary@v1
  with:
    crate-name: my-crate
    target: x86_64-unknown-linux-gnu
    additional-rustflags: -C opt-level=3
```

## Accessing the Built Artifacts

After a successful run, the built artifacts will be available as a downloadable
artifact in the GitHub Actions run.

For binary builds, the artifact will be named `${{ inputs.crate-name }}-${{ inputs.target }}-${{ inputs.features }}`.

For library builds, the artifact will be named `C-Library-${{ inputs.target }}-${{ inputs.features }}`.

To access the artifacts:

1. Navigate to the Actions tab in your repository.
2. Click on the workflow run that built the artifacts.
3. In the "Artifacts" section, you will find the generated artifacts, which you can download.

## Why this Exists?

Building C libraries from Rust projects can be a complex process, especially when
considering different target platforms, compiler flags, and optimizations like PGO.

This action simplifies the process by providing a configurable and reusable workflow
that handles the building of C libraries from Rust projects.

## Contributing

Contributions are welcome! If you encounter any issues or have suggestions for improvements,
please open an issue or submit a pull request in this repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

[devops-test-coverage]: https://github.com/Reloaded-Project/devops-rust-test-and-coverage