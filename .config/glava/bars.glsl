/* Center line thickness (pixels) */
#define C_LINE 1
/* Width (in pixels) of each bar */
#define BAR_WIDTH 4
/* Width (in pixels) of each bar gap */
#define BAR_GAP 2
/* Outline color */
#define BAR_OUTLINE #262626
/* Outline width (in pixels, set to 0 to disable outline drawing) */
#define BAR_OUTLINE_WIDTH 0
/* Amplify magnitude of the results each bar displays */
#define AMPLIFY 280
/* Whether the current settings use the alpha channel */
#define USE_ALPHA 0
/* How strong the gradient changes */
#define GRADIENT_POWER 70
/* Bar color changes with height */
#define GRADIENT (d / GRADIENT_POWER + 1)
/* Bar color - Synced with dynamic accent */
#define COLOR (#019cfb * GRADIENT)
/* Direction that the bars are facing, 0 for inward, 1 for outward */
#define DIRECTION 0
/* Whether to switch left/right audio buffers */
#define INVERT 0
/* Whether to flip the output vertically */
#define FLIP 0
/* Mirror options */
#define MIRROR_YX 0
