{
  description = "Alertas Chile Home Assistant integration (HACS + NixOS)";

  inputs = {
    # Stable 26.05 provides a Home Assistant release newer than the 2026.1
    # floor and still supports x86_64-darwin for the APK research shell.
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
  };

  outputs =
    { self, nixpkgs }:
    let
      linuxSystems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      darwinSystems = [ "x86_64-darwin" ];
      pkgsFor = system: import nixpkgs { inherit system; };

      # Nix store source for the component derivation: ONLY
      # custom_components/ (excludes APKs, findings, .git, etc.).
      componentSrc = nixpkgs.lib.fileset.toSource {
        root = ./.;
        fileset = nixpkgs.lib.fileset.unions [ ./custom_components ];
      };

      mkComponent =
        pkgs: src:
        pkgs.home-assistant.python3Packages.callPackage ./pkgs/alertas-chile-ha/package.nix {
          inherit src;
        };

      mkResearchShell =
        pkgs:
        pkgs.mkShell {
          packages = with pkgs; [
            jdk17
            nodejs_22
            unzip
            curl
            git
          ];
        };

      mkDevShell =
        pkgs:
        let
          haPy = pkgs.home-assistant.python3Packages;
          # NOTE: haPy.python.withPackages resolves `ps` against the
          # interpreter's default pkgs, NOT the HA scope, so reference HA
          # packages absolutely (haPy.<attr>).
          pythonEnv = haPy.python.withPackages (_: [
            haPy.homeassistant
            haPy.pytest
            haPy."pytest-homeassistant-custom-component"
            haPy.pytest-asyncio
            haPy.pytest-aiohttp
            haPy.pytest-cov
            haPy.respx
            haPy.syrupy
          ]);
        in
        pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.ruff
            pkgs.uv
            pkgs.git
            pkgs.jq
            pkgs.nix-output-monitor
          ];

          shellHook = ''
            echo "Alertas Chile HA dev shell"
            echo "  python: $(python --version 2>&1)"
            echo "  HA:     $(python -c 'import homeassistant.const as c; print(c.__version__)' 2>/dev/null || echo 'unavailable')"
            echo "  ruff:   $(ruff --version 2>/dev/null || echo 'unavailable')"
            echo ""
            echo "  pytest tests/          # run integration tests"
            echo "  ruff check . && ruff format --check ."
            echo "  nix build .#alertas-chile-ha   # build Nix package"
          '';
        };
    in
    {
      # Injects alertas_chile into the same namespace nixpkgs uses for
      # packaged custom integrations, so consumers can use the stock HA
      # module:
      #   nixpkgs.overlays = [ inputs.hass-alertas.overlays.default ];
      #   services.home-assistant.customComponents = [
      #     pkgs.home-assistant-custom-components.alertas_chile
      #   ];
      overlays.default = final: prev: {
        home-assistant-custom-components = prev.home-assistant-custom-components.extend (
          _self: _super: {
            alertas_chile = mkComponent final (
              final.lib.fileset.toSource {
                root = ./.;
                fileset = final.lib.fileset.unions [ ./custom_components ];
              }
            );
          }
        );
      };

      packages = nixpkgs.lib.genAttrs linuxSystems (
        system:
        let
          pkgs = pkgsFor system;
        in
        {
          alertas-chile-ha = mkComponent pkgs componentSrc;
          default = self.packages.${system}.alertas-chile-ha;
        }
      );

      devShells =
        nixpkgs.lib.genAttrs linuxSystems (
          system:
          let
            pkgs = pkgsFor system;
          in
          {
            default = mkDevShell pkgs;
            research = mkResearchShell pkgs;
          }
        )
        // nixpkgs.lib.genAttrs darwinSystems (
          system:
          let
            pkgs = pkgsFor system;
          in
          {
            # HA's native dependency chain does not build reliably on darwin;
            # use a Linux dev shell (or CI) for pytest and this shell for APK
            # reverse engineering.
            default = mkResearchShell pkgs;
            research = mkResearchShell pkgs;
          }
        );

      formatter = nixpkgs.lib.genAttrs (linuxSystems ++ darwinSystems) (
        system:
        let
          pkgs = pkgsFor system;
        in
        pkgs.nixfmt
      );
    };
}
