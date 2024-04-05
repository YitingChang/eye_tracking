
%% 
% Add pupi size plot
% Eyelink systems record pupil size data in arbitrary units.
% We need to use the artificial eye to convert arbitrary pupil size units to mm 
clear all;

load 'testData.txt';
screenx = 1920;
screeny = 1080;
zoneSize = 200;
% Calculate scaling factor 
artificial_pupil_width = 3.5; % mm
artificial_pupil_size = 1755; % in area
scaling_factor = artificial_pupil_width/sqrt(artificial_pupil_size);

trials = find(isnan(testData(:, 2)));
trials = vertcat(trials, length(testData));

numTrials = length(trials) - 1

for n = 1 : numTrials
    startNdx = trials(n) + 1;
    stopNdx = trials(n + 1) - 1;
    t = testData(startNdx:stopNdx, 1);
    t = t - min(t);
    dt = diff(t);
    fprintf("trial %d\n", n);

    figure(32);
    clf; hold on;
    title('gaze x, y vs t (msec)');
    plot(t, testData(startNdx:stopNdx, 2), 'r.');
    plot(t, testData(startNdx:stopNdx, 3), 'g.');
    legend('gaze x', 'gaze y')

    figure(33);
    clf; hold on;
    title('gaze data (pixels)');
    plot(testData(startNdx:stopNdx, 2), testData(startNdx:stopNdx, 3), '.');
    xlim([0 screenx]);
    ylim([0, screeny]);
    set(gca, 'YDir', 'reverse')
    viscircles([screenx/2, screeny/2], zoneSize, 'LineWidth', 0.5);

%     figure(34);
%     histogram(dt);

    figure(35)
    clf; hold on;
    title('pupil diameter (mm)');
    pupil_diameter = sqrt(testData(startNdx:stopNdx, 4))*scaling_factor; % in mm
    plot(t, pupil_diameter, 'b.');

    fprintf("Press a key to continue\n");
    pause;
end

