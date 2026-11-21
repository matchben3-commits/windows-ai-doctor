> v0.1/v0.2 历史材料：测试、截图、日期和发布状态保留原轮次；不能当作第三版结果。第三版当前契约与证据见 [v03-contract.md](v03-contract.md) 和 [HANDOFF](../HANDOFF.md)。

# Windows CI fixture correction / Windows CI 测试夹具修正

2026-11-20。首次托管运行 [44753910123](https://github.com/matchben3-commits/windows-ai-doctor/actions/runs/44753910123) 在 Python 3.11 和 3.14 上分别得到 51 通过、5 失败、0 跳过；打包步骤跳过。此失败记录保留，不用本地通过代替。

五项失败均涉及真实 junction 测试的临时目录范围断言。MausBot 在本地通过 Windows `GetShortPathNameW` 为新建的合成临时目录取得真实 8.3 别名，再让测试夹具从该路径创建临时目录，重现同样五项失败。失败位于 `tests/test_boundaries.py` 的 `link.absolute().is_relative_to(self.root.resolve())` 及 `target.absolute().is_relative_to(self.root.resolve())`，在真实被测操作之前就比较了不同的路径表示。

修正仅在 `DoctorFixture.setUp` 中把测试自己创建的临时根目录转换为完整路径，后续夹具、范围断言和清理使用同一位置。没有在产品路径检查中增加 `resolve()`，没有放宽链接拒读策略、删除断言或把失败改成跳过。12 个运行时模块与独立复核候选逐字节相同。

使用相同短路径环境，修正前五项均失败，修正后五项均通过；随后普通本地完整套件为 54 通过、2 权限跳过、0 失败/错误。两次定向运行与完整套件单独计数。证据：[修正前](../evidence/review-v02-ci/fixture-before.json)、[修正后](../evidence/review-v02-ci/fixture-after.json)、[完整本地复跑](../evidence/review-v02-ci/local-tests.json)。

最终托管运行链接及每组结果以版本说明为准。保留先前复核的日期、跳过项和范围：真实 Claude、WSL 内部、所有平台或物理断网不因此得到验证。

The first hosted run failed five junction tests on each Python version. A real Windows short-path temporary directory reproduced those five failures in fixture containment assertions. Canonicalizing only the test-owned temporary root made the same five cases pass. Runtime modules, rejection checks and assertions remain unchanged. The ordinary local suite separately recorded 54 passes and 2 permission skips. Hosted outcomes are linked from the release notes.
