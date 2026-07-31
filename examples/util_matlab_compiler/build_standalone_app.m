projectRoot = fileparts(mfilename('fullpath'));

% Create target build options object, set build properties and build.
buildOpts = compiler.build.StandaloneApplicationOptions(fullfile(projectRoot, "src", "main.m"));
buildOpts.AdditionalFiles = zaber.motion.Helper.getCompilerDependencies();
buildOpts.OutputDir = fullfile(projectRoot, "ZaberStandaloneApp", "output", "build");
buildOpts.Verbose = true;
buildOpts.ExecutableName = "ZaberStandaloneApp";
buildOpts.ExecutableVersion = "1.0.0";
buildOpts.ExecutableIcon = fullfile(projectRoot, "img", "standalone_app_icon.png");

compiler.build.standaloneApplication(buildOpts);
