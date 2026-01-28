fn main() {
    // Build Zig library first
    let status = std::process::Command::new("zig")
        .args(["build", "-Doptimize=ReleaseFast"])
        .current_dir("../zig-core")
        .status()
        .expect("failed to build zig-core");

    assert!(status.success(), "zig-core build failed");

    // Link the static library
    println!("cargo:rustc-link-search=native=../zig-core/zig-out/lib");
    println!("cargo:rustc-link-lib=static=mtcore");

    // Link TagLib (required by zig-core)
    println!("cargo:rustc-link-lib=tag_c");

    // Rebuild if zig sources change
    println!("cargo:rerun-if-changed=../zig-core/src");

    tauri_build::build()
}
