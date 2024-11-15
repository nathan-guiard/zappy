all:
	cd server && cargo build --release && cp target/release/server ../server.bin
	./Godot --path "graphics/" --export-release "Linux/X11" ./gfx 1>&2 2>/dev/null

clean:
	kill $(lsof target/debug/deps/.nfs* | awk 'NR > 1 {print $2}' | sort -u | xargs || true) || true
	cd server && cargo clean
	rm graphics/gfx
