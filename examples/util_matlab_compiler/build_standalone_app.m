projectRoot = fileparts(mfilename('fullfile'));

% Create target build options object, set build properties and build.
buildOpts = compiler.build.StandaloneApplicationOptions(fullfile(projectRoot, "src", "main.m"));
buildOpts.AdditionalFiles = zaber.motion.Helper.getCompilerDependencies();
buildOpts.OutputDir = fullfile(projectRoot, "ZaberTestApp", "output", "build");
buildOpts.Verbose = true;
buildOpts.ExecutableName = "ZaberTestApp";
buildOpts.ExecutableVersion = "1.0.0";
buildOpts.ExecutableIcon = fullfile(projectRoot, "img", "zaber_logo.png");

compiler.build.standaloneApplication(buildOpts);
